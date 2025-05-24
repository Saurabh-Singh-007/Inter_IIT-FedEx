from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value
import csv
# File paths
ULD_FILE = "ULD.txt"
PACKAGE_FILE = "packages.txt"
OUTPUT_FILE = "solution_output.txt"

# Constants
K = 5000  # Cost of spreading priority packages

# Step 1: Read ULD and Package data
def read_uld_data(file_path):
    uld_data = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            uld_data.append({
                "id": row["ULD Identifier"],
                "length": int(row["Length (cm)"]),
                "width": int(row["Width (cm)"]),
                "height": int(row["Height (cm)"]),
                "weight_limit": int(row["Weight Limit (kg)"])
            })
    return uld_data

def read_package_data(file_path):
    package_data = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            package_data.append({
                "id": row["Package Identifier"],
                "length": int(row["Length (cm)"]),
                "width": int(row["Width (cm)"]),
                "height": int(row["Height (cm)"]),
                "weight": int(row["Weight (kg)"]),
                "type": row["Type (P/E)"],
                "delay_cost": int(row["Cost of Delay"]) if row["Cost of Delay"] != '-' else 0
            })
    return package_data

# Read data
uld_data = read_uld_data(ULD_FILE)
package_data = read_package_data(PACKAGE_FILE)

# Step 2: Define problem
prob = LpProblem("ULD_Packing_Optimization", LpMinimize)

# Step 3: Create variables
x = {(p["id"], u["id"]): LpVariable(f"x_{p['id']}_{u['id']}", 0, 1, cat="Binary")
     for p in package_data for u in uld_data}

priority_uld = {u["id"]: LpVariable(f"priority_{u['id']}", 0, 1, cat="Binary") for u in uld_data}

# Variables for coordinates
coords = {(p["id"], u["id"]): {
    "x0": LpVariable(f"x0_{p['id']}_{u['id']}", 0, None, cat="Continuous"),
    "y0": LpVariable(f"y0_{p['id']}_{u['id']}", 0, None, cat="Continuous"),
    "z0": LpVariable(f"z0_{p['id']}_{u['id']}", 0, None, cat="Continuous"),
    "x1": LpVariable(f"x1_{p['id']}_{u['id']}", 0, None, cat="Continuous"),
    "y1": LpVariable(f"y1_{p['id']}_{u['id']}", 0, None, cat="Continuous"),
    "z1": LpVariable(f"z1_{p['id']}_{u['id']}", 0, None, cat="Continuous"),
} for p in package_data for u in uld_data}

# Step 4: Objective Function
prob += lpSum(
    [p["delay_cost"] * (1 - lpSum([x[(p["id"], u["id"])] for u in uld_data])) for p in package_data]
    + [K * priority_uld[u["id"]] for u in uld_data]
)

# Step 5: Constraints
# Weight constraints for each ULD
for u in uld_data:
    prob += lpSum([p["weight"] * x[(p["id"], u["id"])] for p in package_data]) <= u["weight_limit"]

# Ensure priority packages are shipped
for p in package_data:
    if p["type"] == "Priority":
        prob += lpSum([x[(p["id"], u["id"])] for u in uld_data]) == 1

# Link priority packages to ULDs
for u in uld_data:
    prob += priority_uld[u["id"]] >= lpSum([x[(p["id"], u["id"])] for p in package_data if p["type"] == "Priority"]) / len(package_data)

# Spatial constraints
for p in package_data:
    for u in uld_data:
        # Package fits inside the ULD
        prob += coords[(p["id"], u["id"])]["x1"] == coords[(p["id"], u["id"])]["x0"] + p["length"]
        prob += coords[(p["id"], u["id"])]["y1"] == coords[(p["id"], u["id"])]["y0"] + p["width"]
        prob += coords[(p["id"], u["id"])]["z1"] == coords[(p["id"], u["id"])]["z0"] + p["height"]

        prob += coords[(p["id"], u["id"])]["x1"] <= u["length"]
        prob += coords[(p["id"], u["id"])]["y1"] <= u["width"]
        prob += coords[(p["id"], u["id"])]["z1"] <= u["height"]

        # Overlap prevention between packages in the same ULD
        for q in package_data:
            if p["id"] != q["id"]:
                prob += (coords[(p["id"], u["id"])]["x1"] <= coords[(q["id"], u["id"])]["x0"]) | \
                        (coords[(p["id"], u["id"])]["x0"] >= coords[(q["id"], u["id"])]["x1"]) | \
                        (coords[(p["id"], u["id"])]["y1"] <= coords[(q["id"], u["id"])]["y0"]) | \
                        (coords[(p["id"], u["id"])]["y0"] >= coords[(q["id"], u["id"])]["y1"]) | \
                        (coords[(p["id"], u["id"])]["z1"] <= coords[(q["id"], u["id"])]["z0"]) | \
                        (coords[(p["id"], u["id"])]["z0"] >= coords[(q["id"], u["id"])]["z1"])

# Step 6: Solve
prob.solve()

# Step 7: Write Output
with open(OUTPUT_FILE, "w") as output_file:
    total_cost = int(value(prob.objective))
    packed_packages = sum(1 for p in package_data for u in uld_data if value(x[(p["id"], u["id"])]) > 0.5)
    priority_uld_count = sum(1 for u in uld_data if value(priority_uld[u["id"]]) > 0.5)
    output_file.write(f"{total_cost},{packed_packages},{priority_uld_count}\n")

    for p in package_data:
        assigned = False
        for u in uld_data:
            if value(x[(p["id"], u["id"])]) > 0.5:
                assigned = True
                c = coords[(p["id"], u["id"])]
                output_file.write(f"{p['id']},{u['id']},{value(c['x0'])},{value(c['y0'])},{value(c['z0'])},{value(c['x1'])},{value(c['y1'])},{value(c['z1'])}\n")
                break
        if not assigned:
            output_file.write(f"{p['id']},NONE,-1,-1,-1,-1,-1,-1\n")

print(f"Solution written to {OUTPUT_FILE}")
