import pandas as pd
import numpy as np
import itertools
import random
import multiprocessing

# Turn off skip feature for priority
# Height feature
# cofficient increase

# Input: ULD info and set of boxes to be packed
k = 5000
Total_leaving_cost = 29233
priority_num = 88
average_weight = 113.92344497607655

def base_dist(box, point, uld_info, height_map):
    width = box["width"]
    length = box["length"]
    height = box["height"]
    uld_length = uld_info["length"]
    uld_width = uld_info["width"]
    uld_height = uld_info["height"]

    x = point["x"]
    y = point["y"]

    if ((x < 0) or ((x + width) >= uld_width)): return float("inf"), float("inf"), float("inf"), float("inf")
    if ((y < 0) or ((y + length) >= uld_length)): return float("inf"), float("inf"), float("inf"), float("inf")
    if ((point["z"] + height) > uld_height): return float("inf"), float("inf"), float("inf"), float("inf")
    if (height_map[x:x + width, y:y + length].max() > point["z"]) : return float("inf"), float("inf"), float("inf"), float("inf")
    
    area_condition = abs(width * length / (np.sum(height_map == point["z"])) - 1)
    coverage = np.sum((height_map[x:x + width, y:y + length]) == point["z"])
    height_diff = point["z"] - (height_map[x:x + width, y:y + length].sum() / (width * length))
    coverage /= width * length
    coverage += 0.1 * ((height_map[x, y] == point["z"]) + (height_map[x + width, y] == point["z"]) + (height_map[x , y + length] == point["z"]) + (height_map[x + width, y + length] == point["z"]))
    
    return height_map[x:x + width, y:y + length].min(), 1 - coverage, height_diff, area_condition

def orientations(box):
    dimensions = ["length", "width", "height"]
    orientations = list(itertools.permutations([box["length"], box["width"], box["height"]]))

    # Create a DataFrame to store all orientations
    orientation_df = pd.DataFrame(orientations, columns=["length", "width", "height"])

    # Add other attributes to the DataFrame
    for key, value in box.items():
        if key not in dimensions:
            orientation_df[key] = value

    # # Sort according to the base area
    selected_indices = [0, 1, 3, 4]
    orientation_df = orientation_df.sort_values(by="height", ascending=False).iloc[selected_indices].reset_index(drop=True)
    return orientation_df

def calculate_cost(box, point, uld_info, height_map):
    height = box["height"]

    """Calculates fitness for placing a box at a given point."""
    min_height, coverage, height_diff, area_condition = base_dist(box, point, uld_info, height_map)
    if (coverage > 0.3) : return float("inf")
    avg_gap = height_diff / uld_info["height"]
    max_gap = (point["z"] - min_height) / height
    cost = 0.075 * (max_gap + (point["z"] / uld_info["height"])) + 0.2 * avg_gap / uld_info["height"] + 0.05 * area_condition + 0.6 * coverage
    return cost

def update_height_map(box, point, height_map):
    """Updates the height map after placing a box."""
    s_x = point["x"]
    s_y = point["y"]
    height_map[s_x:s_x + box["width"], s_y:s_y + box["length"]] = point["z"] + box["height"]

def fit_boxes_to_uld(uld_info, box_info, alloted_weight, alloted_volume):
    uld_length = uld_info["length"]
    uld_width = uld_info["width"]
    uld_height = uld_info["height"]
    uld_weight_limit = uld_info["weight_limit"]
    uld_volume = uld_info["volume"]

    # Initialize height map and potential points and placements
    height_map = np.zeros((uld_width + 1, uld_length + 1))
    potential_points = [
        {"x": 0, "y": 0, "z": 0},
        {"x": 0, "y": uld_length - 1, "z": 0},
        {"x": uld_width - 1, "y": 0, "z": 0},
        {"x": uld_width - 1, "y": uld_length - 1, "z": 0}
    ]
    placements = []
    left_boxes = []

    for i in range(len(box_info)):
        # random_chance = random.uniform(0, 1)
        box = box_info.iloc[i]
        all_orient = orientations(box)
        
        if (alloted_weight + box["weight"] > uld_weight_limit): continue
        if (alloted_volume + box["volume"] > uld_volume): continue

        candidate_point = []
        best_neg_fitness = float("inf")
        best_point = None
        best_point_orientation = None

        # Evaluate all potential points
        for point in potential_points:
            if ((point["z"] < uld_height / 3) and (box["weight"] < average_weight) and (box["type"] == "Economy")): continue
            if ((point["z"] > 2 * uld_height / 3) and (box["weight"] > average_weight) and (box["type"] == "Economy")): continue
            if (point["x"] >= uld_width or point["y"] >= uld_length or point["z"] > uld_height or height_map[point["x"], point["y"]] != point["z"]): 
                potential_points.remove(point)
                continue
            for orient in range(len(all_orient)):
                box_orient = all_orient.iloc[orient]
                iterations = [
                    {"x": point["x"], "y": point["y"], "z": point["z"]},
                    {"x": point["x"] - box_orient["width"], "y": point["y"], "z": point["z"]},
                    {"x": point["x"], "y": point["y"] - box_orient["length"], "z": point["z"]},
                    {"x": point["x"] - box_orient["width"], "y": point["y"] - box_orient["length"], "z": point["z"]},
                ]

                for iter_point in iterations:
                    neg_fitness = calculate_cost(box_orient, iter_point, uld_info, height_map)
                    if neg_fitness < best_neg_fitness:
                        best_neg_fitness = neg_fitness
                        candidate_point = [(iter_point, orient)]
                    elif neg_fitness == best_neg_fitness:
                        candidate_point.append((iter_point, orient))
        
        # print(box["id"], best_neg_fitness)

        # Place the box if a valid point is found
        if (len(candidate_point)>0 and (best_neg_fitness < 5)):
            best_point, best_point_orientation = random.choice(candidate_point)
            box = all_orient.iloc[best_point_orientation]

            alloted_weight += box["weight"]
            alloted_volume += box["volume"]
            dimens = (box["width"], box["length"], box["height"])

            p_x = best_point["x"]
            p_y = best_point["y"]
            p_z = best_point["z"]

            placements.append({"box_id": box['id'], "placement": (p_x, p_y, p_z), "dimensions": dimens, "weight": box["weight"], "type": box["type"], "cost": box["cost"], "ULD" : uld_info["id"]})
            update_height_map(box, best_point, height_map)

            # Add new potential points
            New_points = [
                {"x": p_x + box["width"], "y": p_y, "z": p_z},
                {"x": p_x, "y": p_y + box["length"], "z": p_z},
                {"x": p_x, "y": p_y, "z": p_z + box["height"]},
                {"x": p_x + box["width"], "y": p_y + box["length"], "z": p_z},
                {"x": p_x, "y": p_y + box["length"], "z": p_z + box["height"]},
                {"x": p_x + box["width"], "y": p_y, "z": p_z + box["height"]}, 
                {"x": p_x + box["width"], "y": p_y + box["length"], "z": p_z + box["height"]}
            ]
            potential_points.extend(New_points)
        else: left_boxes.append(box)
    
    box_info = pd.DataFrame(left_boxes)
    left_boxes = []

    for i in range(len(box_info)):
        # random_chance = random.uniform(0, 1)
        box = box_info.iloc[i]
        all_orient = orientations(box)
        
        if (alloted_weight + box["weight"] > uld_weight_limit): continue
        if (alloted_volume + box["volume"] > uld_volume): continue

        candidate_point = []
        best_neg_fitness = float("inf")
        best_point = None
        best_point_orientation = None

        # Evaluate all potential points
        for point in potential_points:
            # if ((point["z"] < uld_height / 3) and (box["weight"] < average_weight) and (box["type"] == "Economy")): continue
            # if ((point["z"] > 2 * uld_height / 3) and (box["weight"] > average_weight) and (box["type"] == "Economy")): continue
            if (point["x"] >= uld_width or point["y"] >= uld_length or point["z"] > uld_height or height_map[point["x"], point["y"]] != point["z"]): 
                potential_points.remove(point)
                continue
            for orient in range(len(all_orient)):
                box_orient = all_orient.iloc[orient]
                iterations = [
                    {"x": point["x"], "y": point["y"], "z": point["z"]},
                    {"x": point["x"] - box_orient["width"], "y": point["y"], "z": point["z"]},
                    {"x": point["x"], "y": point["y"] - box_orient["length"], "z": point["z"]},
                    {"x": point["x"] - box_orient["width"], "y": point["y"] - box_orient["length"], "z": point["z"]},
                ]

                for iter_point in iterations:
                    neg_fitness = calculate_cost(box_orient, iter_point, uld_info, height_map)
                    if neg_fitness < best_neg_fitness:
                        best_neg_fitness = neg_fitness
                        candidate_point = [(iter_point, orient)]
                    elif neg_fitness == best_neg_fitness:
                        candidate_point.append((iter_point, orient))
        
        # print(box["id"], best_neg_fitness)

        # Place the box if a valid point is found
        if (len(candidate_point)>0 and (best_neg_fitness < 5)):
            best_point, best_point_orientation = random.choice(candidate_point)
            box = all_orient.iloc[best_point_orientation]

            alloted_weight += box["weight"]
            alloted_volume += box["volume"]
            dimens = (box["width"], box["length"], box["height"])

            p_x = best_point["x"]
            p_y = best_point["y"]
            p_z = best_point["z"]

            placements.append({"box_id": box['id'], "placement": (p_x, p_y, p_z), "dimensions": dimens, "weight": box["weight"], "type": box["type"], "cost": box["cost"], "ULD" : uld_info["id"]})
            update_height_map(box, best_point, height_map)

            # Add new potential points
            New_points = [
                {"x": p_x + box["width"], "y": p_y, "z": p_z},
                {"x": p_x, "y": p_y + box["length"], "z": p_z},
                {"x": p_x, "y": p_y, "z": p_z + box["height"]},
                {"x": p_x + box["width"], "y": p_y + box["length"], "z": p_z},
                {"x": p_x, "y": p_y + box["length"], "z": p_z + box["height"]},
                {"x": p_x + box["width"], "y": p_y, "z": p_z + box["height"]}, 
                {"x": p_x + box["width"], "y": p_y + box["length"], "z": p_z + box["height"]}
            ]

            potential_points.extend(New_points)
        else: left_boxes.append(box)
    
    return alloted_weight, alloted_volume, pd.DataFrame(left_boxes), placements

def placement_all_uld(priority_df_temp, uld_data, num_uld):
    iteration_placement = []
    
    for i in range(num_uld):
        uld = uld_data.iloc[i]
        volume_util = 0
        weight_util, volume_util, left_boxes, placement = fit_boxes_to_uld(uld, priority_df_temp, 0, 0)
        priority_df_temp = left_boxes

        iteration_placement.append([weight_util, volume_util, placement])
    return iteration_placement

def cost_calculation(Placements):
    cost = Total_leaving_cost
    num = []
    for uld in Placements:
        uld_placement = uld[2]
        priority = 0
        for box in uld_placement:
            if (box["type"] == "Priority"): priority += 1
            else: cost -= box["cost"]
        if (priority>0): cost += k
        num.append(priority)
    
    if (sum(num) < priority_num): return num, 60000
    return num, cost

def worker_task(iter, packages, uld_sorted, num_uld):
    # Each thread works on a copy of priority_df
    priority_df_temp = packages.copy()
    iter_placement = placement_all_uld(priority_df_temp, uld_sorted, num_uld)
    num_priority, cost = cost_calculation(iter_placement)
    iter_placement.append([num_priority, cost, []])
    return iter_placement, cost

def best_placement(iterations, packages_df, uld_sorted, num_uld):
    packages = packages_df
    final_placement = []
    all_costs = []

    with multiprocessing.Pool(processes=min(12, iterations)) as pool:
        # Submit tasks to the thread pool
        results = [ pool.apply_async(worker_task, args=(iter, packages.copy(), uld_sorted, num_uld)) for iter in range(iterations) ]
        # Collect results as they complete
        cnt = 0
        for result in results:
            iter_placement, cost = result.get()

            if len(final_placement) == 0 or final_placement[num_uld][1] > iter_placement[num_uld][1]:
                final_placement = iter_placement

            if (cost<60000): 
                all_costs.append(cost)
                # print(iter_placement[num_uld])
                cnt += iter_placement[num_uld][0][3]
        if (len(all_costs)): print(cnt / len(all_costs))
    
    return all_costs, final_placement