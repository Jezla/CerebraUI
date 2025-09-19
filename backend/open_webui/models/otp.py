import logging

import uuid
from typing import Optional
from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel
from sqlalchemy import Column, String, BigInteger, Integer, Boolean

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# OTP DB Model
####################
class OtpModel(Base):
    __tablename__ = "otp"
    id = Column(String, primary_key=True)
    email = Column(String)
    otp = Column(String)
    attempts = Column(Integer)
    is_used = Column(Boolean)
    token = Column(String)

####################
# OTP Model
####################
class Otp(BaseModel):
    id: Optional[str] = None
    email: str
    otp: str
    attempts: int
    is_used: bool
    token: Optional[str] = None

####################
# OTP Form
####################
class verifyOtpForm(BaseModel):
    email: str
    otp: str
    token: str

class verifyTokenForm(BaseModel):
    email: str
    token: str

class ResetPasswordForm(BaseModel):
    email: str
    new_password: str
    token: str

####################
# OTP Table
####################
class otpTable:
    def insert_new_otp(self, email: str, otp: str, token: str) -> Optional[OtpModel]:
        try:
            with get_db() as db:
                id = str(uuid.uuid4())
                otp_model = OtpModel(
                    id=id,
                    email=email,
                    otp=otp,
                    attempts=0,
                    is_used=False,
                    token=token
                )
                
                db.add(otp_model)
                db.commit()
                db.refresh(otp_model)
                
                if otp_model:
                    return otp_model
                else:
                    return None
        except Exception as e:
            log.error(f"Failed to insert OTP: {e}")
            return None

    def delete_otp_by_email(self, email: str) -> bool:
        try:
            with get_db() as db:
                db.query(OtpModel).filter_by(email=email).delete()
                db.commit()
                return True
        except Exception as e:
            log.error(f"Failed to delete OTP: {e}")
            return False
    
    def get_otp_by_email(self, email: str) -> Optional[OtpModel]:
        try:
            with get_db() as db:
                otp = db.query(OtpModel).filter_by(email=email).first()
                if otp:
                    return otp
                return None
        except Exception as e:
            log.error(f"Failed to get OTP: {e}")
            return None
    
    def update_otp_by_email(self, email: str, otp: str, token: str) -> bool:
        try:
            with get_db() as db:
                result = db.query(OtpModel).filter_by(email=email).update({
                    "otp": otp, 
                    "attempts": 0,
                    "token": token
                })
                db.commit()
                return True if result == 1 else False
        except Exception as e:
            log.error(f"Failed to update OTP: {e}")
            return False

    def increment_attempts(self, email: str) -> bool:
        try:
            with get_db() as db:
                otp = db.query(OtpModel).filter_by(email=email).first()
                if otp:
                    otp.attempts += 1
                    db.commit()
                    return True
                return False
        except Exception as e:
            log.error(f"Failed to increment attempts: {e}")
            return False
    
    def mark_as_used(self, email: str) -> bool:
        try:
            with get_db() as db:
                result = db.query(OtpModel).filter_by(email=email).update({"is_used": True})
                db.commit()
                return True if result == 1 else False
        except Exception as e:
            log.error(f"Failed to mark OTP as used: {e}")
            return False

otp = otpTable()
