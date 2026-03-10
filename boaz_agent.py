import smtplib, ssl, os, base64, hmac, hashlib, time
from email.mime.text import MIMEText
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---------------------------------------------------------
# CONFIGURATION — EDIT THESE TWO LINES ONLY
# ---------------------------------------------------------
SHARED_KEY = bytes.fromhex("2e53539b24bc32ac70aa068aa402bacb07104eead9299ab84467c1c774592698")
SENDER_EMAIL = "YOUR_EMAIL@gmail.com"
SENDER_PASS = "YOUR_APP_PASSWORD"
# ---------------------------------------------------------

BOAZ_ID = "BOAZ_PILAR_01"
JACHIN_ID = "JACHIN_GATE_01"
MMS_ENDPOINT = "4096667081@mms.cricketwireless.net"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


# ---------------------------------------------------------
# CRYPTOGRAPHY
# ---------------------------------------------------------
def derive_session_key(nonce_b, nonce_j):
    return hmac.new(SHARED_KEY, nonce_b + nonce_j, hashlib.sha256).digest()


def aesgcm_encrypt(k_sess, plaintext, nonce):
    aesgcm = AESGCM(k_sess)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    cipher = base64.b64encode(ct[:-16]).decode()
    tag = base64.b64encode(ct[-16:]).decode()
    return cipher, tag


# ---------------------------------------------------------
# MMS SENDER
# ---------------------------------------------------------
def send_mms(body: str):
    msg = MIMEText(body)
    msg["To"] = MMS_ENDPOINT
    msg["From"] = SENDER_EMAIL
    msg["Subject"] = "Helix-Sync"

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as server:
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, MMS_ENDPOINT, msg.as_string())

    print("Boaz → sent:", body)


# ---------------------------------------------------------
# BOAZ AGENT
# ---------------------------------------------------------
class BoazAgent:
    def __init__(self):
        self.state = "IDLE"
        self.k_sess = None
        self.last_contact = 0
        self.seq = 1
        self.nonce_b = None

    # -----------------------------------------------------
    # HANDSHAKE
    # -----------------------------------------------------
    def initiate_handshake(self):
        print("\nBoaz → Sending HELIX_INIT")
        self.nonce_b = os.urandom(16)
        frame = f"HELIX_INIT|{BOAZ_ID}|{self.nonce_b.hex()}|{int(time.time())}|{self.seq}"
        send_mms(frame)
        self.state = "WAIT_ACK"
        self.last_contact = time.time()

    # -----------------------------------------------------
    # SIMULATED ACK (until you wire real inbound path)
    # -----------------------------------------------------
    def simulate_ack(self):
        print("Boaz → Simulating HELIX_ACK (for now)")
        nonce_j = os.urandom(16)
        self.k_sess = derive_session_key(self.nonce_b, nonce_j)
        print("Boaz → Session key established.")
        self.state = "SECURE"
        self.last_contact = time.time()
        self.seq += 1

    # -----------------------------------------------------
    # SECURE SIGNAL SENDER
    # -----------------------------------------------------
    def send_signal(self, token="S1"):
        if self.state != "SECURE":
            print("Boaz → Not SECURE; cannot send signal.")
            return

        nonce = os.urandom(12)
        cipher_b64, tag_b64 = aesgcm_encrypt(self
