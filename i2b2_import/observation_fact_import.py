from pandas import DataFrame
from datetime import datetime


########################################################################################################################
# SETTINGS
########################################################################################################################

PATIENT_NUM_COL = 'RID'
ENCOUNTER_NUM_COL = 'MRICode'
PROVIDER_ID_COL = 'ORIGPROT'
START_DATE_COL = 'ScanDate'
DEFAULT_MODIFIER_DC = '@'
DIM_COLUMNS = [PATIENT_NUM_COL, ENCOUNTER_NUM_COL, PROVIDER_ID_COL, START_DATE_COL]


########################################################################################################################
# PUBLIC FUNCTIONS
########################################################################################################################

def csv2db(file_path, db_conn, src):
    """
    Import brain features and other observation facts data from a CSV file into the I2B2 DB schema.
    :param file_path: Path to the CSV file.
    :param db_conn: Connection to the I2B2 DB.
    :param src: Data source (e.g. CHUV, ADNI, PPMI, etc).
    :return:
    """
    data = DataFrame.from_csv(file_path, index_col=False)
    column_headers = list(data)
    concept_columns = set(column_headers) - set(DIM_COLUMNS)
    for index, row in data.iterrows():
        patient_src_num = row[PATIENT_NUM_COL]
        encounter_src_num = row[ENCOUNTER_NUM_COL]
        provider_id = row[PROVIDER_ID_COL]
        start_date = _eu_date_to_datime(row[START_DATE_COL])
        modifier_cd = DEFAULT_MODIFIER_DC
        for concept_cd in concept_columns:
            val = row[concept_cd]
            valtype_cd = _find_type(val)
            if valtype_cd == 'N':
                tval_char = 'E'
                nval_num = float(val)
            else:
                tval_char = val
                nval_num = None
            patient_num = _get_patient_num(db_conn, patient_src_num, src)
            encounter_num = _get_encounter_num(db_conn, encounter_src_num, src)
            _save_observation(db_conn, encounter_num, concept_cd, provider_id, start_date, patient_num, modifier_cd,
                              valtype_cd, tval_char, nval_num)


########################################################################################################################
# PUBLIC FUNCTIONS
########################################################################################################################

def _get_patient_num(db_conn, patient_ide, patient_ide_source):
    patient_ide = str(patient_ide)
    patient = db_conn.db_session.query(db_conn.PatientMapping).filter_by(
        patient_ide_source=patient_ide_source, patient_ide=patient_ide).first()
    if not patient:
        patient = db_conn.PatientMapping(patient_ide_source=patient_ide_source, patient_ide=patient_ide,
                                         patient_num=db_conn.new_patient_num())
        db_conn.db_session.add(patient)
        db_conn.db_session.commit()
    return patient.patient_num


def _get_encounter_num(db_conn, encounter_ide, encounter_ide_source):
    encounter_ide = str(encounter_ide)
    visit = db_conn.db_session.query(db_conn.EncounterMapping).filter_by(
        encounter_ide_source=encounter_ide_source, encounter_ide=encounter_ide).first()
    if not visit:
        visit = db_conn.EncounterMapping(encounter_ide_source=encounter_ide_source, encounter_ide=encounter_ide,
                                         encounter_num=db_conn.new_encounter_num())
        db_conn.db_session.add(visit)
        db_conn.db_session.commit()
    return visit.encounter_num


def _eu_date_to_datime(d):
    return datetime.strptime(d, "%d.%m.%Y")


def _save_observation(db_conn, encounter_num, concept_cd, provider_id, start_date, patient_num, modifier_cd, valtype_cd,
                      tval_char, nval_num):
    observation = db_conn.db_session.query(db_conn.ObservationFact) \
        .filter_by(encounter_num=encounter_num, concept_cd=concept_cd, provider_id=provider_id, start_date=start_date,
                   patient_num=patient_num, modifier_cd=modifier_cd) \
        .first()
    if not observation:
        observation = db_conn.ObservationFact(
            encounter_num=encounter_num, concept_cd=concept_cd, provider_id=provider_id, start_date=start_date,
            patient_num=patient_num, modifier_cd=modifier_cd, valtype_cd=valtype_cd, tval_char=tval_char,
            nval_num=nval_num, import_date=datetime.now()
        )
        db_conn.db_session.add(observation)
        db_conn.db_session.commit()


def _find_type(val):
    try:
        float(val)
        return 'N'
    except ValueError:
        return 'T'