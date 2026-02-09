from archicad import ACConnection
from archicad import Types as act

# ---------------------------------
# PRIPOJENIE K ARCHICADU
# ---------------------------------
conn = ACConnection.connect()
assert conn

acc = conn.commands

# ---------------------------------
# PREVOD mm -> m
# ---------------------------------
def mm(val):
    return val / 1000.0

# ---------------------------------
# ROZMERY STENY (mm)
# ---------------------------------
start_point = (0.0, 0.0)  # Začiatok steny
end_point = (mm(5000), 0.0)  # Koniec steny
height = mm(3000)  # Výška steny
thickness = mm(300)  # Hrúbka steny

# ---------------------------------
# VYTVORENIE WALL ELEMENTU
# ---------------------------------
wall = act.Wall(
    begC=act.Coordinate(start_point[0], start_point[1]),
    endC=act.Coordinate(end_point[0], end_point[1]),
    height=height,
    thickness=thickness,
    structure=act.WallStructure.Basic,
    buildingMaterial=acc.GetAttributes('BuildingMaterial')[0]  # Použitie prvého dostupného materiálu
)

# ---------------------------------
# VLOŽENIE DO PROJEKTU
# ---------------------------------
acc.CreateElements([wall])

print("✅ Stena bola úspešne vytvorená.")
