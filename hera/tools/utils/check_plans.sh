#!/bin/bash
rm -f file_cycle.txt file_plans.txt
CYCLE_NUMBER=$(jq ".cycles|length" TestCycle.json)
for ((i=0;i<${CYCLE_NUMBER};i++))
do
   PLAN_NUMBER=$(jq ".cycles[$i].plans|length" TestCycle.json)
   for ((j=0;j<${PLAN_NUMBER};j++))
   do
     jq ".cycles[$i].plans[$j]" TestCycle.json >> file_cycle.txt
   done
done


PLANS_NUMBER=$(jq ".plans|length" TestPlans.json)
for ((i=0;i<${PLANS_NUMBER};i++))
do
  jq ".plans[$i].name" TestPlans.json >> file_plans.txt
done

cat file_cycle.txt file_plans.txt | grep -v ^$ | sort | uniq -u
