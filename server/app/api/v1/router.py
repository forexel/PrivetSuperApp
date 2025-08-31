@router.get("/ping")
def ping():
    return {"pong": True}
