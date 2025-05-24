import pandas as pd
import numpy as np
import random
import time

def at_least_two_same(set1, set2):
    common = set(set1).intersection(set2)
    return len(common)>1

def combine_sets(set1, set2):
    common = set(set1).intersection(set2)
    combined = [val for val in common]
    if (len(combined) == 3):
        idx = 4 
        min_dimen = 10000000
        for i in range(3):
            if combined[i] < min_dimen:
                min_dimen = combined[i]
                idx = i
        combined[idx] *= 2
    else:
        combined.append(0)
        for val in set1: 
            if val not in common: combined[2] += val
        for val in set2: 
            if val not in common: combined[2] += val
    return tuple(combined)

def processing(boxes):
    combined_data = []
    deleted_box = []
    for _, box1 in boxes.iterrows():
        if (box1["id"] in deleted_box): continue
        deleted_box.append(box1["id"])
        same_dimen = []
        dimen1 = (box1["length"], box1["width"], box1["height"])
        for _, box2 in boxes.iterrows():
            if (box2["id"] in deleted_box): continue
            dimen2 = (box2["length"], box2["width"], box2["height"])
            if at_least_two_same(dimen1, dimen2): same_dimen.append(box2)
        
        if (len(same_dimen)>0):
            box2 = random.choice(same_dimen)
            deleted_box.append(box2["id"])
            new_id = ", ".join([box1["id"], box2["id"]])
            dimen2 = (box2["length"], box2["width"], box2["height"])
            final_dimen = combine_sets(dimen1, dimen2)
            box1["id"] = new_id
            box1["length"] = final_dimen[0]
            box1["width"] = final_dimen[1]
            box1["height"] = final_dimen[2]
            box1["weight"] = box1["weight"] + box1["weight"]
            box1["cost"] = box1["cost"] + box1["cost"]
            box1["volume"] = box1["volume"] + box1["volume"]
        combined_data.append(box1)
    return pd.DataFrame(combined_data)

def super_items(boxes):
    while(True):
        temp = processing(boxes)
        if (len(temp) == len(boxes)): break
        boxes = temp
    return boxes

def all_data():
    # Define the file path
    file_path = 'Challange_FedEx1.txt'

    # Initialize variables for ULDs and Packages
    uld_lines = []
    package_lines = []
    extracting_uld = False
    extracting_package = False

    # Read the file line by line
    with open(file_path, "r") as file:
        for line in file:
            if "ULD attributes" in line:
                extracting_uld = True
                extracting_package = False
                continue
            if "Package attributes" in line:
                extracting_uld = False
                extracting_package = True
                continue
            if extracting_uld and line.strip():
                uld_lines.append(line.strip())
            if extracting_package and line.strip():
                package_lines.append(line.strip())

    # Create DataFrame for ULDs
    uld_header = uld_lines[0].split(",")
    uld_data = [line.split(",") for line in uld_lines[1:]]
    uld_df = pd.DataFrame(uld_data, columns=uld_header)

    uld_numeric_columns = ["Length (cm)", "Width (cm)", "Height (cm)", "Weight Limit (kg)"]
    for col in uld_numeric_columns:
        if col in uld_df.columns:
            uld_df[col] = pd.to_numeric(uld_df[col], errors="coerce")

    # Create DataFrame for Packages
    package_header = package_lines[0].split(",")
    package_data = [line.split(",") for line in package_lines[1:]]
    package_df = pd.DataFrame(package_data, columns=package_header)
    k = 5000

    package_numeric_columns = ["Length (cm)", "Width (cm)", "Height (cm)", "Weight (kg)", "Cost of Delay"]
    for col in package_numeric_columns:
        if col in package_df.columns:
            package_df[col] = pd.to_numeric(package_df[col], errors="coerce")

    # Rename columns for consistency
    uld_new_df = uld_df.rename(columns={
        "ULD Identifier": "id",
        "Length (cm)": "length",
        "Width (cm)": "width",
        "Height (cm)": "height",
        "Weight Limit (kg)": "weight_limit"
    })

    package_new_df = package_df.rename(columns={
        "Package Identifier": "id",
        "Length (cm)": "length",
        "Width (cm)": "width",
        "Height (cm)": "height",
        "Weight (kg)": "weight",
        "Type (P/E)": "type",
        "Cost of Delay": "cost"
    })

    # Add volume columns
    package_new_df["volume"] = package_new_df.width * package_new_df.length * package_new_df.height
    uld_new_df["volume"] = uld_new_df.width * uld_new_df.height * uld_new_df.length

    priority_df = package_new_df[package_new_df["type"] == "Priority"].reset_index(drop=True)
    economy_df = package_new_df[package_new_df["type"] == "Economy"].reset_index(drop=True)

    # Creating Super items
    priority_df = super_items(priority_df)
    economy_df = super_items(economy_df)

    # Sorting
    # ULD fitness function
    uld_vol_coeff = 0.5
    uld_weight_limit_coeff = 0.5
    avg_uld_weight_limit = uld_new_df["weight_limit"].mean()
    avg_uld_volume = uld_new_df["volume"].mean()

    def calculate_fitness_uld(uld): 
        return (uld_vol_coeff * uld["volume"] / avg_uld_volume + uld_weight_limit_coeff * uld["weight_limit"] / avg_uld_weight_limit)

    # Sorting ULDs by fitness
    uld_sorted = uld_new_df.copy()
    uld_sorted["fitness"] = uld_sorted.apply(lambda uld: calculate_fitness_uld(uld), axis=1)
    uld_sorted = uld_sorted.sort_values(by="fitness", ascending=False).reset_index(drop=True)

    # Boxes fitness function
    box_vol_coeff = 0.1
    box_weight_coeff = 0.1
    box_cost_coeff = 1 - box_vol_coeff - box_weight_coeff
    avg_box_weight = package_new_df["weight"].mean()
    avg_box_volume = package_new_df["volume"].mean()
    avg_box_cost = economy_df["cost"].mean()

    def calculate_fitness_box(box):
        fitt = box_vol_coeff * box["volume"] / avg_box_volume + box_weight_coeff * box["weight"] / avg_box_weight
        if (box["type"] == "Priority"): fitt += box_cost_coeff
        else: fitt += box_cost_coeff * box["cost"] * (avg_box_volume / box["volume"]  + avg_box_weight / box["weight"]) / (avg_box_cost * 2)
        fitt *= random.uniform(0.9, 1.1)
        return fitt

    def sort_boxes(box_df):
        box_df["fitness"] = box_df.apply(
            lambda box: calculate_fitness_box(box), axis=1
        )
        return box_df.sort_values(by="fitness", ascending=False).reset_index(drop=True)
    
    priority_df = sort_boxes(priority_df)
    economy_df = sort_boxes(economy_df)

    return uld_sorted, priority_df, economy_df

# uld_sorted, priority_df, economy_df = all_data()
# print(economy_df.head(50))
# priority_df.to_csv('Priority.csv', index=False)
# economy_df.to_csv('Economy.csv', index=False)