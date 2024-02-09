import math

bs_lat = 45.478671
bs_long = 9.232550

mirror_lat = 45.478694
mirror_long = 9.232083

ue_lat = 45.47753
ue_long = 9.23470

# dist_mirror_UE_x = (mirror_long-ue_long)*40075*math.cos((mirror_lat+ue_lat)*math.pi/360)/360
dist_mirror_UE_x = 0.180

dist_mirror_UE_z_calculated = (ue_lat - bs_lat) * 40075 / 360
print(dist_mirror_UE_x * 1000)
print(dist_mirror_UE_z_calculated * 1000)

# ue_lat = float(input("Enter UE coordinates: "))
# ue_long = float(input("Enter UE coordinates: "))
# bs_x = float(input("Enter base station x coordinate: \n"))
# bs_y = float(input("Enter base station y coordinate: \n"))
# bs_z = float(input("Enter base station z coordinate: \n"))

bs_x = bs_z = bs_y = float(0)

# m_x = float(input("Enter mirror x coordinate: \n"))
# m_y = float(input("Enter mirror y coordinate: \n"))
# m_z = float(input("Enter mirror z coordinate: \n"))
m_x = float(-2)
m_z = m_y = float(0)

# dist_mirror_UE_x = float(input("Enter distance between mirror and UE on x axis"))


# m_elevation = float(input("Enter mirror elevation tilt in degrees: \n"))
m_elevation = 0
# m_alpha = float(input("Enter mirror inclination tilt in degrees: \n"))
for m_alpha in [0, 30, 60, 15, 16, 17, 18]:
    epsilon = math.atan2((bs_z - m_z), (bs_x - m_x))  # radians, mirror-BS beam disalignment (elevation)
    alpha = math.atan2((bs_y - m_y), (bs_x - m_x))  # radians, mirror-BS beam disalignment (azimuth)

    phi_elevation = 90 - math.degrees(epsilon) - m_elevation  # degrees
    phi_alpha = 90 - math.degrees(alpha) - m_alpha  # degrees

    varA = phi_elevation + m_elevation  # degrees
    varB = phi_alpha - m_alpha  # degrees

    dist_mirror_UE_y = 0  # my - ue_y

    dist_mirror_UE_z = dist_mirror_UE_x / math.tan(math.radians(varB))

    print("Mirror tilt: " + str(m_alpha))
    print("Mirror UE angle: " + str(varB))
    print("Mirror UE distance in z-axis: " + str(dist_mirror_UE_z * 1000))
    print("-----------------")
    