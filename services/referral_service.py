from database.db import connect
def create_referral(patient_id, facility, urgency):
    con=connect()
    con.execute("INSERT INTO referrals(patient_id,facility,urgency) VALUES (?,?,?)",(patient_id,facility,urgency))
    con.commit(); con.close()
