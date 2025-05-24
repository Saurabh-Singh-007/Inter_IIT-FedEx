import pandas as pd
import numpy as np

def parse_and_save(placements):
    all_uld_placement = pd.DataFrame([])
    priority_boxes = placements[-1][0]
    final_cost = placements[-1][1]
    for i in range(len(placements)-1):
        w, v, p = placements[i]
        if (len(p) == 0): continue
        box_data = []
        for b in p: box_data.append(b)
        box_data = pd.DataFrame(box_data)
        box_place = pd.DataFrame(box_data["placement"].tolist(), columns=["p_x", "p_y", "p_z"])
        box_dimen = pd.DataFrame(box_data["dimensions"].tolist(), columns=["width", "length", "height"])
        box_data = pd.concat([box_data.drop(columns=["placement", "dimensions"]), box_place, box_dimen], axis=1)
        box_data["weight_util"] = w
        box_data["volume_util"] = v
        box_data["priority_boxes"] = priority_boxes[i]
        all_uld_placement = pd.concat([all_uld_placement, box_data], ignore_index=True)
    
    all_uld_placement["total_cost"] = final_cost
    # print(all_uld_placement)
    all_uld_placement.to_csv('Final_Placements.csv', index= False)

def extract_placements():
    placements = []
    priority_boxes = []
    data = pd.read_csv('Final_Placements.csv')
    data["placement"] = data.apply(lambda row: (row['p_x'], row['p_y'], row['p_z']), axis=1)
    data["dimensions"] = data.apply(lambda row: (row['width'], row['length'], row['height']), axis=1)
    grouped = data.groupby('ULD')
    Total_cost = data["total_cost"].iloc[0]
    # print(len(grouped))
    for key, uld_group in grouped:
        uld_data = []
        priority_boxes.append(uld_group["priority_boxes"].iloc[0])
        weight_util = uld_group["weight_util"].iloc[0]
        volume_util = uld_group["volume_util"].iloc[0]
        for i in range(len(uld_group)):
            row = uld_group.iloc[i]
            box_placement = {
                "box_id": row['box_id'], 
                "placement": row["placement"], 
                "dimensions": row["dimensions"], 
                "weight": row["weight"], 
                "type": row["type"], 
                "cost": row["cost"], 
                "ULD" : row["ULD"]
            }
            uld_data.append(box_placement)
        placements.append([weight_util, volume_util, uld_data])
    
    indexes = [4, 5, 2, 3, 0, 1]
    placements = [placements[i] for i in indexes]
    placements.append([priority_boxes, Total_cost, []])
    # print(placements)
    print(priority_boxes)
    return placements
    # print(data)
