from pydantic import BaseModel, Field
from typing import  Union, Optional
from typing import List

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    email: str
    
class NewUserForm(BaseModel):
    email: str
    username: str
    password: str

class UserInDB(User):
    password: str
    id_user: int

class SetNewSport(BaseModel):
    sportList: list
    zkusenostiList: list

class Phase(BaseModel):
    nazev: Optional[str] = Field(None, description="Název kterým chceme fázi pojmenovat")
    id_faze_nadrazene: Optional[int] = Field(None, description="ID fáze která je této nadřazená")
    id_sport: Optional[int] = Field(None, description="Sport ke kterému fáze náleží")
    id_zkusenost: Optional[int] = Field(None, description="Zkušenot kterou uživatel s tímto sportem má")    
    active: Optional[int] = Field(1, description="Smazání či obnovení fáze", ge=0, le=1)

class SetPhase(BaseModel):
    id_faze: int = Field(int, description='ID přidané fáze')
    nazev: str = Field(str, description='Název fáze')
    id_faze_nadrazene: Optional[int] = Field(None, description='ID fáze této nadřazené')
    id_user: int = Field(int, description='Uživatel pro kterého fáze platí')
    id_sport: int = Field(int, description='Sport pod který fáze spadá')
    id_zkusenost: int = Field(int, description='Zkušenost, kterou uživatel v dané fazi se sportem má')
    next: Union[List['SetPhase'], list] = Field([], description='List objektů fází které jsou této podřazené')
    sub_sport: Union[List['SubSport'], list] = Field([], description='List sportů které jsou tomuto podřazené')
    exercise: Union[List['Exercise'], list] = Field([], description='List cviků které se k tomuto sportu dají přiřadit')
    attributes: Union[List['Aributy'], list] = Field([], description='Pole atributů přiřazených k danému sportu')
    assigned_exercise : List['GetPhaseExercise'] = Field([], description='List přiřazených cviků')
    assigned_attributes : List['GetPhaseAttributes'] = Field([], description='List přiřazených cviků')
    assigned_exercise_for_attributes:  List['GetPhaseExercise'] = Field([], description='List přiřazených cviků pro nadrazenou fazi')

class GetPhaseAttributes(BaseModel):
    id_faze_atribut: int = Field(int, description="ID tabulky atributy_data")
    id_atribut_data: int = Field(int, description="Cizí klíč na tabulku atributy_data, ukazuje který záznam je v této fázi")
    id_atribut_data_nadrazeny: int = Field(int, description="ID nadřazeného atributu tomuto")
    id_faze_cvik: int
    hodnota: float = Field(float, description="Hodnota atributu")
    id_atribut: int = Field(int, description="ID přiřazovaného atributu")
    nazev: str = Field(str, description="Název atributu")
    next: List['GetPhaseAttributes']
    active: Optional[int] = Field(1, description="Smazání či obnovení fáze", ge=0, le=1)




class Sport(BaseModel):
    id_sport: int
    nazev: str
    id_sport_nadrazene: int


class SubSport(Sport):
    sub_sport: Union[List['SubSport'], list] = []

class Exercise(BaseModel):
    id_cvik: int
    nazev: str
    doporucena_zkusenost: int

class SetPhaseExercise(BaseModel):
    id_cvik: int
    id_faze: int
    active: Optional[int] = Field(1, description="Ukazatel zda je cvik v této fázi aktivní", ge=0, le=1)

class GetPhaseExercise(SetPhaseExercise):
    id_faze_cvik: int
    nazev: str
    doporucena_zkusenost: int

class Aributy(BaseModel):
    id_atribut: int
    id_atribut_nadrazeny: int
    nazev: str
    next: Union[List['Aributy'], list] = Field([], description='Podřazené atributy')


class setAttributesForm(BaseModel):
    hodnota: float
    id_atribut: int
    id_atribut_nadrazeny: int
    id_faze_cvik: int

class setAtributesForPhase(BaseModel):
    attributes: List[setAttributesForm]

class AttributesData(BaseModel):
    id_atributy_data: Optional[int]	= Field(None, description='Primární klíč v tabulce atributy_data')
    id_faze_cvik: Optional[int] = Field(None, description='Primární klíč tabulky faze_cvik, určuje pro jaký cvik ve fázi atribut patří')
    hodnota: float	
    id_atribut: int	
    id_atribut_data_nadrazeny: int
    

class AttributesPhase(BaseModel):
    id_faze_atribut: Optional[int]	= Field(None, description='Podřazené atributy')
    id_faze: int
    id_atribut_data: int
    id_faze_cvik: int
    active: Optional[int] = Field(1, description="Ukazatel zda je atribut aktivní pro tuto fázi", ge=0, le=1)

GetPhaseAttributes.update_forward_refs()
SetPhase.update_forward_refs()
SubSport.update_forward_refs()
Aributy.update_forward_refs()
Exercise.update_forward_refs()
