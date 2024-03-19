from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status
from models import *
from typing import Annotated, Union
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from logic import *
from settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, CURSOR, CONNECTION
import mysql.connector



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

def checkIfExists(email: str) -> bool:
    SELECT = """
    Select * from `user` where email = %s ;
    """
    CURSOR.execute(SELECT, params=[email])
    if CURSOR.fetchone():
        return False
    return True

def create_user(user: NewUserForm) -> bool:
    # Hash the password using the provided plaintext password
    hashed_password = get_password_hash(user.password)
    if not checkIfExists(user.email):
        return False

    INSERT = """
    INSERT INTO user (username, email, password) VALUES (%s, %s, %s);
    """
    try:
        CURSOR.execute(INSERT, (user.username, user.email, hashed_password))
        CONNECTION.commit()
        return True  # User creation successful
    except mysql.connector.Error as err:
        print("Error creating user:", err)
        CONNECTION.rollback()
        return False  # User creation failed

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(email: str):
    SELECT = """
    SELECT username, email, password, id_user from user where email = %s
    """
    CURSOR.execute(SELECT, params=[email])
    user = CURSOR.fetchone()
    
    if user:
        user_dict = {'username': user[0], 'email': user[1], 'password': user[2], 'id_user': user[3]}
        return UserInDB(**user_dict)


def authenticate_user(username: str, password: str):
    user = get_user(email=username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.username)
    if user is None:
        raise credentials_exception
    return user



@app.post("/token/", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/signIn/", response_model=Token)
async def create_new_user(
    form_data: NewUserForm
):
    if not create_user(form_data):
        credentials_exception = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


@app.get("/getActivePhase/")
async def getPhase(
    current_user: Annotated[UserInDB, Depends(get_current_user)]
) -> List[SetPhase]:
    return getLatestPhaseDB(current_user.id_user)

@app.get("/getSports/")
async def getSports() -> SetNewSport:
    return SetNewSport(sportList=getSportsDB(), zkusenostiList=getZkusenosti()) 

@app.post("/setSport/")
async def setSport(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    phase: Phase,
    ) -> SetPhase:

    return setPhase(id_zkusenost=phase.id_zkusenost,
                     id_faze_nadrazene=phase.id_faze_nadrazene,
                       id_user=current_user.id_user,
                         id_sport=phase.id_sport,
                          nazev=phase.nazev)
     

@app.patch("/patchPhase/{id_faze}/")
async def patchPhase(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    phase: Phase,
    id_faze: int
    ) -> bool:
    return patchPhaseDB(id_faze=id_faze, **phase.dict())

@app.post("/setPhaseExercise/")
async def setPhaseExercise(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    phaseExercise: SetPhaseExercise,
    ) -> GetPhaseExercise:
    return setPhaseExerciseDB(phaseExercise)


@app.post("/setPhaseAttribut/Phase/{id_faze}/")
async def setPhaseAttribute(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    phaseAttributes: setAtributesForPhase,
    id_faze: int
    ) -> List[GetPhaseAttributes]:

    return setPhaseAttributeDB(phaseAttributes, id_faze)



