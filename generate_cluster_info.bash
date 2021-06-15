#!/bin/bash

c1=103
c2=0
c3=0

printf "node0: $c1,\n"
for (( i = 0; i < $c1; i++ ))
do
   nodei=$(printf "node%03d" $i)
   printf "\t$nodei: $c2,\n"
   for (( j = 0; j < $c2; j++ ))
   do
      nodej=$(printf "$nodei$j")
      printf "\t\t$nodej: $c3,\n"
      for (( k = 0; k < $c3; k++ ))
      do
         nodek=$(printf "$nodej$k")
         printf "\t\t\t$nodek: 0,\n"
      done
   done
done
