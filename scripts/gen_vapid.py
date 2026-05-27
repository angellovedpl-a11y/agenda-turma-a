from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

key = ec.generate_private_key(ec.SECP256R1())
priv = key.private_numbers().private_value.to_bytes(32, "big")
pub = key.public_key().public_bytes(
    serialization.Encoding.X962,
    serialization.PublicFormat.UncompressedPoint,
)
print("PRIVATE:", base64.urlsafe_b64encode(priv).rstrip(b"=").decode())
print("PUBLIC:", base64.urlsafe_b64encode(pub).rstrip(b"=").decode())
