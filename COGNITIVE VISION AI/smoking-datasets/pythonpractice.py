# Python

# 1) Variables & Data types
# 2) Strings & Condistional Statements
# 3) Lists & Tuples
# 4) Dictonary & Sets
# 5) Loops
# 6) Functions & Recursion
# 7) File i/o
# 8) Oops



# Lect 1

# for print
# name= "yasir"
# print(name)

# for input
# na=str(input("your name?"))
# print(na)

# to check class of variable
# na=str(input("your name?"))
# print(type(na))


# Lect 2
# name=input("name?")
# if(name =="ahsan"):
#     print("boy")
# else:
#     print("girl")


# Lect 3

# list

# name=["yasir","ammar","aashir"]
# print(name)
# name.insert(2,"ali")
# print(name)

# tuple

# name=("ali","ammar")
# print(name)

# Questions

# 1
# a=[1,3,2,1]
# c=a.copy()
# c.reverse()
# if(c == a):
#     print("its palindrome")
# else:
#     print("not palindrome")    

# 2
# tup=("C","D","A","A","B","B","A")
# print(tup.count("A"))

# 3
# list=["C","D","A","A","B","B","A"]
# list.sort()
# print(list)



# Lect 4

# Dictonary={
#     "name":"yasir",
#     "age":21,
#     "course":"python",
# }
# print(Dictonary)

# Dictonary={}# empty dict

# nested
# Dictonary={
#     "name":"yasir",
#     "age":21,
#     "course":{
#         "phy":89,
#         "chem":90,
#     }
# }
# print(Dictonary)

# its mutable so we can add or change dictonary
# Dictonary={
#     "name":"yasir",
#     "age":21,
#     "course":"python",
# }
# Dictonary["name"]="Soomro"
# Dictonary["age"]="22"
# print(Dictonary)




# Dictonary methods

# no of keys
# Dictonary={
#     "name":"yasir",
#     "age":21,
#     "course":{
#         "phy":89,
#         "chem":90,
#     }
# }
# print(Dictonary.keys())
# or
# print(list(Dictonary.keys()))

# # no of values
# print(Dictonary.values())
# or
# print(list(Dictonary.values()))

# no of item(return all key values pairs as tuple)
# print(Dictonary.items())
# or
# print(list(Dictonary.items()))

# get
# Dictonary={
#     "name":"yasir",
#     "age":21,
#     "course":{
#         "phy":89,
#         "chem":90,
#     }
# }
# print(Dictonary["name"])
# or
# print(Dictonary.get("name"))
# if 
# # print(Dictonary["name2"]) error
# print(Dictonary.get("name2")) no error return (none)


# update

# Dictonary={
#     "name":"yasir",
#     "age":21,
#     "course":"python",
# }
# Dictonary.update({"city":"lahore","country":"Pakistan"})
# print(Dictonary)

# or


# new_dic={
#     "city":"lahore",
#     "country":"pakistan",
# }
# Dictonary.update(new_dic)
# print(Dictonary)




# SETS
# unhashable:means mutable (sets,list,dict)
# unordered/no duplicate value
# Sets are mutable but each element in set must be unique and immutable
# we can store 
# int
# float
# bool
# str
# tuple
# we cannot store 
# list
# dict
# bcz they are mutable

# example

# collection={1,2,"yasir",3,"ali",2,3}
# print(collection)
# print(type(collection))#set
# print(len(collection))#5 bcz no duplicate

# collection= set()#empty set


# Sets methods:

# set.add(element)

# collection= set()
# collection.add(1)
# collection.add(3)
# collection.add("Ali")
# print(collection)


# set.remove(element)

# collection= {1,2,3,4,5}
# collection.remove(3)
# collection.remove(2)
# print(collection)


# set.clear()

# collection= {1,2,3,4,5}
# collection.clear()#empty the set
# print(collection)

# set.pop()

# collection= {1,2,3,4,5}
# collection.pop()
# collection.pop()
# print(collection) it removes a random value


# set.union()

# collection={1,2,3,4,5}
# collection2={2,3,5,6,7}
# print(collection.union(collection2))



# set.intersection()

# collection={1,2,3,4,5}
# collection2={2,3,5,6,7}
# print(collection.intersection(collection2))


# Example question

# Q:1) Store following word meaning in python dictionary
# table:"a piece of furniture","list of facts and figures"
# cat:"a small animal"

# Dictonary={
#     "table":["a piece of furniture","list of facts and figures"],
#     "cat":"a small animal",
# }
# print(Dictonary)

# Q:2) You are given a list of subjects for students.Assume one classroom is requires for 1 subject. How many classrooms are needed by all students?(python,java,c++,python, javascript,java,python,java,c++,c)

# set={"python","java","c++","python", "javascript","java","python","java","c++","c"}
# print(len(set))


# Q:3) write a program to enter marks of 3 subjects from user and store them in dictonary.Start with an empty dictonary & add one by one. use subjects name as key and marks as value?


# Dictonary={}

# marks=str(input("Enter Math marks"))
# Dictonary.update({"math":marks})
# marks=str(input("Enter eng Marks"))
# Dictonary.update({"eng":marks})
# marks=str(input("Enter phy Marks"))
# Dictonary.update({"phy":marks})

# print(Dictonary)


#  Q:4) Figure out a way to store 9 and 9.0 as seperate values in set(you can take help to built-in data types)?

# # 1st answer
# set={9,"9.0"} using strings
# print(set)

# # 2nd answer(using built-in datatypes)
# set={
#     ("int",9),
#     ("float",9.0) in pairs using tuple
# }
# print(set)




# Lect 5
# Loops


# While Loop
# Q:1) print no from 1 to 100
# num=1
# while num<=100:
#     print("hello world")
#     num+=1
    
# Q:2) print no from 100 to 1
# num=100
# while num>=1:
#     print("hello world")
#     num+=1

# Q:3) Print table of any number

# i=1
# n=int(input("Enter number \n"))
# while i<=10:
#     print(n*i)
#     i+=1

# Q:4)  print elements of following (1,4,9,16,25,36,49,64,81,100)

# i=1
# while i<=10:
#     print(i*i)
#     i+=1

#   Q:5)  print elements of following list[1,4,9,16,25,36,49,64,81,100]

# list=[1,4,9,16,25,36,49,64,81,100]
# index=0
# while index < len(list):
#     print(list[index])
#     index+=1

# Q:6 search for number x in this  tuple using loop(1,4,9,16,25,36,49,64,81,100)

# tup=(1,4,9,16,25,36,49,64,81,100)
# index=0
# n=36
# while index < len(tup):
#     if(tup[index]==n):
#         print("found",index)
#     else:
#         print("finding... ")
#     index+=1

