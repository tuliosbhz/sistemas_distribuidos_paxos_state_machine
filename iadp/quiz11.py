#%%
str1 = input()
count_spaces = 0
for i in range(0, len(str1)):
    if ' ' == str1[i]:
        count_spaces += 1
print("Number of spaces = %d" % (count_spaces))

#%%
numbers = input()
inverted_num = numbers[::-1]
print(int(inverted_num))
#%%
alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
plain_text = input()
cypher_key = int(input())
cypher_text = ""

for i in range(0,len(plain_text)):
    index = alpha.index(plain_text[i])
    new_index = index + cypher_key
    cypher_text += alpha[new_index]

print(cypher_text)




# %%
