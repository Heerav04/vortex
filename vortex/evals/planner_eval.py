import json
import asyncio
from pathlib import Path
import sys
import time

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from core.planner import VortexPlanner
from core.planner_v2 import VortexPlannerV2
from core.memory import VortexMemory

async def compare_planners():
    print("Initializing Planners for Evaluation...")
    mem = VortexMemory()
    planner_v1 = VortexPlanner(mem)
    planner_v2 = VortexPlannerV2(mem)

    eval_file = BASE_DIR / "evals" / "planner_eval_set.jsonl"
    
    v1_correct = 0
    v2_correct = 0
    total = 0
    
    print(f"{'Query':<30} | {'V1 Tool':<15} | {'V2 Tool':<15} | {'Match Expected'}")
    print("-" * 80)
    
    with open(eval_file, "r") as f:
        for line in f:
            if not line.strip(): continue
            total += 1
            data = json.loads(line)
            query = data["query"]
            exp_tool = data["expected_tool"]
            exp_action = data["expected_action"]
            
            # Run V1
            plan_v1 = planner_v1.create_plan(query)
            v1_t = plan_v1.steps[0].tool if plan_v1.steps else "none"
            v1_a = plan_v1.steps[0].action if plan_v1.steps else "none"
            if v1_t == exp_tool and v1_a == exp_action:
                v1_correct += 1
                
            # Run V2
            result_v2 = await planner_v2.create_plan_async(query)
            v2_t = "none"
            v2_a = "none"
            if result_v2:
                plan_v2, conf = result_v2
                if plan_v2.steps:
                    v2_t = plan_v2.steps[0].tool
                    v2_a = plan_v2.steps[0].action
                if v2_t == exp_tool and v2_a == exp_action:
                    v2_correct += 1
                    
            print(f"{query[:28]:<30} | {v1_t+'.'+v1_a:<15} | {v2_t+'.'+v2_a:<15} | V1:{v1_t==exp_tool} V2:{v2_t==exp_tool}")

    print("-" * 80)
    print(f"Planner V1 Routing Accuracy: {v1_correct}/{total} ({(v1_correct/total)*100:.1f}%)")
    print(f"Planner V2 Routing Accuracy: {v2_correct}/{total} ({(v2_correct/total)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(compare_planners())
