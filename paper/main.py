import pandas as pd
import numpy as np
import time
from pp_placement import best_placement
from pp_placement_improvement import best_placement_improvement
from visualization import visualize_container
from sorting import all_data
from save import parse_and_save, extract_placements

iterations = 100
num_uld = 6
Solve = False
def count(place):
    cnt = 0
    for ids in place: 
        box_ids = ids["box_id"].split(',')  
        cnt+= len(box_ids)
    return cnt

def main():
    #uld_sorted, priority_df, economy_df = all_data()
    economy_df = pd.read_csv("Economy.csv")
    priority_df = pd.read_csv("Priority.csv")
    uld_sorted = pd.read_csv("ULd.csv")

    packages_df = pd.concat([priority_df, economy_df])
    start_time = time.time()
    
    if (Solve): all_costs, final_placement = best_placement(iterations, packages_df, uld_sorted, num_uld)
    else: 
        final_placement = extract_placements()
        #all_costs, final_placement = best_placement_improvement(iterations, packages_df, uld_sorted, num_uld, final_placement)  -> Uncomment this line to use the improvement function
    
    end_time = time.time()

    print()
    print()
    print("Best Solution:")
    total_weight_util = 0
    total_volume_util = 0
    total_boxes_fitted = 0

    for i in range(num_uld):
        uld = uld_sorted.iloc[i]
        weight_util, volume_util, placement = final_placement[i]
        total_volume_util += volume_util
        total_weight_util += weight_util
        total_boxes_fitted += count(placement)
        print("Number of boxes in",uld["id"], "is", count(placement))
        print("Weight Utilization of",uld["id"], "is", 100 * weight_util / uld["weight_limit"])
        print("Volume Utilization of",uld["id"], "is", 100 * volume_util / uld["volume"])
        print()
        if (final_placement[num_uld][1] < 41000): visualize_container(uld, placement)
        

    print()
    print("Average Weight Utilization is", 100 * total_weight_util / uld_sorted["weight_limit"].sum())
    print("Average Volume Utilization is", 100 * total_volume_util / uld_sorted["volume"].sum())
    print("Total boxes fitted is", total_boxes_fitted)
    print("Number of Priority boxes is", final_placement[num_uld][0])
    print("Leaving Cost is", final_placement[num_uld][1])
    print()

    #if (Solve):
    if (sum(final_placement[num_uld][0])!=88): print("All priority not fit")
    else: print("Average cost across all iterations:", 1.0* sum(all_costs) / len(all_costs), len(all_costs))
    
    print("Runtime:", end_time - start_time)
    print("Average runtime per iteration:", (end_time - start_time) / iterations)

    if (final_placement[num_uld][1] < 33512):
        parse_and_save(final_placement)

if __name__ == "__main__":
    main()