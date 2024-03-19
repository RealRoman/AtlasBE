from settings import CURSOR, CONNECTION
import pandas as pd
import numpy as np
from models import  Exercise, SetPhase, GetPhaseExercise, SetPhaseExercise, Aributy,  setAtributesForPhase, AttributesData, AttributesPhase, GetPhaseAttributes
from typing import List

def getLatestPhaseDB(is_user: int) -> List[SetPhase]:
    final = []

    SELECT = """
    SELECT * FROM faze where id_user = %s and active = 1
    """
    CURSOR.execute(SELECT, params=[is_user])
    res = CURSOR.fetchall()
    df = pd.DataFrame(res).replace({np.nan: None})
    if df.empty:
        return []
    df.columns = [i[0] for i in CURSOR.description]

    SELECT = """
    select * from sport s;
    """
    CURSOR.execute(SELECT)
    df_sport = pd.DataFrame(CURSOR.fetchall())
    df_sport.columns = [i[0] for i in CURSOR.description]

    def getSubSport(id_sport: int):
        rows = df_sport.query('id_sport_nadrazene == @id_sport')
        if rows.empty:
            return []

        holder = []
        for i, val in rows.iterrows():
            if val['id_sport'] == val['id_sport_nadrazene']:
                continue
            node = {key: val[key] for key in df_sport.columns}
            node['sub_sport'] = getSubSport(val['id_sport'])
            holder.append(node)
        return holder

    # ZISKA VSECHNY SU SPORTY A JEJICH ATRIBUTY CI CVIKY
    def getTree(id_nadrazene: int):
        rows = df.query('id_faze_nadrazene == @id_nadrazene & id_faze != @id_nadrazene')
        if rows.empty:
            return []

        holder = []
        for i, val in rows.iterrows():
            node = {key: val[key] for key in df.columns}
            node['next'] = getTree(val['id_faze'])
            node['sub_sport'] = getSubSport(val['id_sport'])
            node['exercise'] = getExercises(val['id_sport'])
            node['attributes'] = getAtributes(val['id_sport'])
            node['assigned_exercise'] = getAssignedExercise(val['id_faze'])
            node['assigned_exercise_for_attributes'] = getAssignedExercise(id_nadrazene)
            node['assigned_attributes'] = getAssignedAttribute(val['id_faze'])
            holder.append(node)
        return holder
    
    for i, val in df[df['id_faze_nadrazene'].isnull()].iterrows():
        node = {key: val[key] for key in df.columns}
        node['next'] = getTree(val['id_faze'])
        node['sub_sport'] = getSubSport(val['id_sport'])
        node['exercise'] = getExercises(val['id_sport'])
        node['attributes'] = getAtributes(val['id_sport'])
        node['assigned_exercise'] = getAssignedExercise(val['id_faze'])
        node['assigned_exercise_for_attributes'] = getAssignedExercise(val['id_faze'])
        node['assigned_attributes'] = getAssignedAttribute(val['id_faze'])
        final.append(SetPhase(**node))  
    
    return final

def getAssignedAttribute(idFaze: int) -> List[GetPhaseAttributes]:
    """
    Vrátí všechny aktivní atributy pro danou fázi
    """
    final = []
    SELECT = """
    select 
    fa.id_faze_atribut,
    fa.id_atribut_data,
    ad.id_atribut,
    ad.hodnota,
    ad.id_atribut_data_nadrazeny,
    a.nazev,
    fa.id_faze_cvik,
    fa.active 
    from faze_atribut fa
    left join atributy_data ad on ad.id_atributy_data = fa.id_atribut_data 
    left join atributy a on a.id_atribut = ad.id_atribut 
    where fa.id_faze  = %s and fa.active = 1 
    """
    CURSOR.execute(SELECT, params=[idFaze])
    df = pd.DataFrame(CURSOR.fetchall())
    if df.empty:
        return []
    df.columns = [i[0] for i in CURSOR.description]


    def getTree(idNadrazenehoAtributu: int) -> List[GetPhaseAttributes]:
        holder = []
        dfFiltered = df[df['id_atribut'] == idNadrazenehoAtributu].query('id_atribut != id_atribut_data_nadrazeny')
        if dfFiltered.empty:
            return []
        for key, val in dfFiltered.iterrows():
            holder.append(GetPhaseAttributes(id_atribut_data_nadrazeny=val['id_atribut_data_nadrazeny'],
                                        id_atribut_data=val['id_atribut_data'],
                                        id_faze_atribut=val['id_faze_atribut'],
                                        id_atribut=val['id_atribut'],
                                        id_faze_cvik=val['id_faze_cvik'],
                                        hodnota=val['hodnota'],
                                        nazev=val['nazev'],
                                        active=1,
                                        next=getTree(val['id_atribut_data_nadrazeny'])))
    for key, val in df.query('id_atribut == id_atribut_data_nadrazeny').iterrows():
        
        final.append(GetPhaseAttributes(id_atribut_data_nadrazeny=val['id_atribut_data_nadrazeny'],
                                        id_atribut_data=val['id_atribut_data'],
                                        id_faze_atribut=val['id_faze_atribut'],
                                        id_faze_cvik=val['id_faze_cvik'],
                                        id_atribut=val['id_atribut'],
                                        hodnota=val['hodnota'],
                                        nazev=val['nazev'],
                                        active=1,
                                        next=getTree(val['id_atribut_data_nadrazeny'])))
    return final


def getSportsDB() -> list | pd.DataFrame:
    SELECT = """
    select * from sport s where s.id_sport = s.id_sport_nadrazene;
    """
    CURSOR.execute(SELECT)
    return CURSOR.fetchall()



def getZkusenosti() -> list:
    SELECT = """
    select id_zkusenost,popis  from zkusenost z 
    """
    CURSOR.execute(SELECT)
    return CURSOR.fetchall()

def setPhase(nazev: str, id_sport: int, id_zkusenost: int, id_user: int, id_faze_nadrazene: int | None = None ) -> SetPhase:
    INSERT = """
    insert into faze (faze.nazev, faze.id_faze_nadrazene, faze.id_user, faze.id_sport, faze.id_zkusenost) values (%s, %s ,%s , %s, %s)
    """
    CURSOR.execute(INSERT, params=[nazev,id_faze_nadrazene, id_user, id_sport, id_zkusenost])
    CONNECTION.commit()
    return getPhase(CURSOR.lastrowid)

def getPhase(phase_id: int):
    SELECT = """
    SELECT
    f.id_faze, 
    f.nazev, 
    f.id_faze_nadrazene,
    f.id_user,
    f.id_sport,
    f.id_zkusenost,
    f.active
    FROM faze f 
    WHERE f.id_faze = %s;
    """
    CURSOR.execute(SELECT, params=[phase_id])
    res = pd.DataFrame(CURSOR.fetchall())
    res.columns = [i[0] for i in CURSOR.description]
    final = res.to_dict('records')[0]   
    SELECT = """
    select * from sport s;
    """
    CURSOR.execute(SELECT)
    df_sport = pd.DataFrame(CURSOR.fetchall())
    df_sport.columns = [i[0] for i in CURSOR.description]

    def getSubSport(id_sport: int):
        rows = df_sport.query('id_sport_nadrazene == @id_sport')
        if rows.empty:
            return []

        holder = []
        for i, val in rows.iterrows():
            if val['id_sport'] == val['id_sport_nadrazene']:
                continue
            node = {key: val[key] for key in df_sport.columns}
            node['sub_sport'] = getSubSport(val['id_sport'])
            holder.append(node)
        return holder
    
    final['sub_sport'] = getSubSport(final['id_sport'])
    # dalsi faze budou vzdy prazdne protoze je prave vytvorene
    final['next'] = []
    final['exercise'] = getExercises(final['id_sport'])
    final['attributes'] = getAtributes(final['id_sport'])
    final['assigned_exercise'] = getAssignedExercise(final['id_faze'])
    final['assigned_exercise_for_attributes'] = getAssignedExercise(final['id_faze_nadrazene'])
    final['assigned_attributes'] = getAssignedAttribute(final['id_faze'])
    return SetPhase(**final)

def getExercises(id_sport: int) -> List[Exercise]:
    """
    Vrátí cviky které jsou pro sport určeny, pokud je sport teprve ve fázi, vrátí prazdný list
    """
    SELECT = """
    select 
    sc.id_sport,
    c.id_cvik,
    c.nazev as nazev_cviku,
    c.doporucena_zkusenost
    from sport_cvik sc
    left join cvik c on c.id_cvik = sc.id_cvik 
    where sc.id_sport  = %s
    """
    CURSOR.execute(SELECT, params=[id_sport])
    res = CURSOR.fetchall()
    # pokud není v tabulce vrátí prázdný list
    if not res:
        return []
    final = []
    # uložení do datafremu
    df_exercise = pd.DataFrame(res)
    df_exercise.columns = [i[0] for i in CURSOR.description]
    for i, val in df_exercise.iterrows():
        final.append(Exercise(id_cvik=val['id_cvik'],
                              nazev=val['nazev_cviku'],
                              doporucena_zkusenost=val['doporucena_zkusenost']))

    return final

def getAtributes(id_sport:int) -> list:
    final = []
    SELECT = """
    select 
    sa.id_sport_atributy,
    sa.id_sport,
    a.id_atribut,
    a.nazev, 
    a.id_atribut_nadrazeny 
    from sport_atributy sa 
    left join atributy a on a.id_atribut = sa.id_atribut 
    where sa.id_sport = %s
    """
    CURSOR.execute(SELECT, [id_sport])
    res = CURSOR.fetchall()
    if not res:
        return []
    df_exercise_vytridene = pd.DataFrame(res)
    df_exercise_vytridene.columns = [i[0] for i in CURSOR.description]

    def getTree(id_nadrazene: int) -> list:
        new_df = df_exercise_vytridene.query('id_atribut_nadrazeny == @id_nadrazene & id_atribut_nadrazeny != id_atribut')
        holder = []
        if new_df.empty:
            return []
        for i, val in new_df.iterrows():
            holder.append(Aributy(id_atribut=val['id_atribut'],nazev=val['nazev'],next=getTree(val['id_atribut']),id_atribut_nadrazeny=val['id_atribut_nadrazeny']))
        return holder
    
    

    for i, val in df_exercise_vytridene.iterrows():
        final.append(Aributy(id_atribut=val['id_atribut'],nazev=val['nazev'],next=getTree(val['id_atribut']),id_atribut_nadrazeny=val['id_atribut_nadrazeny']))
    return final

def getAssignedExercise(id_phase: int) -> List[GetPhaseExercise]:
    """
    Vrátí list všech aktivních cviků v dané fázi
    """
    SELECT = """
    SELECT 
    fc.id_faze_cvik,
    fc.id_faze,
    fc.active,
    c.id_cvik,
    c.nazev,
    c.doporucena_zkusenost
    FROM faze_cvik fc left join cvik c on c.id_cvik = fc.id_cvik
    WHERE id_faze = %s and active = 1
    """
    CURSOR.execute(SELECT, params=[id_phase])
    return [GetPhaseExercise(**dict(zip(CURSOR.column_names, row))) for row in CURSOR.fetchall()]
    
def patchPhaseDB(**kwargs) -> bool:
    id_faze = kwargs.pop('id_faze')
    # ocisteni kwargs od hosnot ktere jsou None
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    set_clause = ', '.join(f'{column} = %s' for column in kwargs.keys())
    values = list(kwargs.values()) + [id_faze]
    UPDATE = f"""
    UPDATE faze SET {set_clause} WHERE id_faze = %s
    """

    try:
        CURSOR.execute(UPDATE, params=values)
        CONNECTION.commit()
        return True
    except Exception as e:
        return False
    
def setPhaseExerciseDB(phaseExercise: SetPhaseExercise) -> GetPhaseExercise:
    """
    Zapisuje do tabulky `faze_cvik`, která ukládá informaci pro který kterou fázi je daný cvik aktivní
    """
    INSERT = """
    INSERT INTO faze_cvik (id_cvik, id_faze) VALUES (%s, %s)
    """
    CURSOR.execute(INSERT, params=[phaseExercise.id_cvik, phaseExercise.id_faze])
    CONNECTION.commit()
    return getPhaseExerciseDB(CURSOR.lastrowid)

def getPhaseExerciseDB(id_faze_cvik: int) -> GetPhaseExercise:
    """
    Vypisuje z tabulky `faze_cvik`
    """
    SELECT = """
    SELECT 
    *
    FROM faze_cvik fc left join cvik c on c.id_cvik = fc.id_cvik  
    WHERE fc.id_faze_cvik = %s
    """
    CURSOR.execute(SELECT, params=[id_faze_cvik])
    fetch = CURSOR.fetchone()
    res = {val[0]: fetch[i]  for i, val in enumerate(CURSOR.description, 0)}
    return GetPhaseExercise(**res)

def setPhaseAttributeDB(fazeAtribut: setAtributesForPhase, idFaze: int):
    for obj in fazeAtribut.attributes:
        attData = insertAtributyData(attributesData=AttributesData(hodnota=obj.hodnota, id_atribut= obj.id_atribut, id_atribut_data_nadrazeny=obj.id_atribut_nadrazeny))
        attPhase = insertPhaseAttributes(phaseAttributes=AttributesPhase(id_faze=idFaze, id_atribut_data=attData, id_faze_cvik=obj.id_faze_cvik))
    return getAssignedAttribute(idFaze)

def insertAtributyData(attributesData: AttributesData) -> int:
    INSERT = f"""
    INSERT into atributy_data (hodnota, id_atribut, id_atribut_data_nadrazeny) VALUES (%s, %s, %s)
    """
    CURSOR.execute(INSERT, params=[attributesData.hodnota, attributesData.id_atribut, attributesData.id_atribut_data_nadrazeny])
    CONNECTION.commit()
    return CURSOR.lastrowid

def insertPhaseAttributes(phaseAttributes: AttributesPhase) -> int:
    INSERT = f"""
    INSERT into faze_atribut (id_faze, id_atribut_data, id_faze_cvik) VALUES (%s, %s, %s)
    """
    CURSOR.execute(INSERT, params=[phaseAttributes.id_faze, phaseAttributes.id_atribut_data, phaseAttributes.id_faze_cvik])
    CONNECTION.commit()
    return CURSOR.lastrowid