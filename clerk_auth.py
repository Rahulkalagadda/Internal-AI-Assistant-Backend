import requests
from jose import jwt, JWTError

# Clerk configuration for your project
CLERK_ISSUER = "https://bold-pug-61.clerk.accounts.dev"
CLERK_JWKS_URL = f"{CLERK_ISSUER}/.well-known/jwks.json"
CLERK_AUDIENCE = "https://api.clerk.com"  # Backend API URL as audience

# JWKS Public Key (for reference, not used directly)
# -----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtt4GiLjBRmBxMwJ0yWOP
# fGDbn5XtLPIOIBiwStX0a2z6bdujEc4g3FDmhJA14T1U8sz9OIs5VrWqWXB8KGn3
# M2hztZ6yNjyZmNinqlyzGvWYYc04eEqOuIMHn2sONpXwFCMM8pXjlLH8w+JkspGK
# HuMkZ6u2/H6UB6ZEPYeL0ErQ4AI9sOp1XhiMI8rTSktap6gP/iGvXCYmmqh+nj8w
# 7q0wGW2XMN5jQmjlLuelSJEPHfhdkZLclQ5KuXr2VVVjLnMXtUCC9GP0vC0PzWEc
# Rldyv/pTwhBaWTdDR5qZ21uQ6eEUZzHmRRlfJlZ3JI4glpZnEVEUbhJPEZUxNcWn
# 6wIDAQAB
# -----END PUBLIC KEY-----

_jwks = None

def get_jwks():
    global _jwks
    if _jwks is None:
        resp = requests.get(CLERK_JWKS_URL)
        resp.raise_for_status()
        _jwks = resp.json()
    return _jwks

def verify_clerk_token(token: str):
    jwks = get_jwks()
    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=CLERK_AUDIENCE,
            issuer=CLERK_ISSUER,
            options={"verify_at_hash": False}
        )
        return payload
    except JWTError as e:
        raise Exception(f"Invalid Clerk JWT: {e}") 