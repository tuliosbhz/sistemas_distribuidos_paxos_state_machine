

#%% 
# 11.01 Invert the characters of a sentence
string1 = "Todo mundo está certo"
string2 = ""
print(string2)
new_index = 0
for i in range(len(string1)-1,-1,-1):
    string2 += string1[i]
    new_index += 1
print(string2)
# %%
#11.02 Count the number of vowels of a sentence
string1 = "Misto é muito bom"
vowels = "aeiouáéíóúãẽĩõũ"
count = 0
for i in range(0, len(string1)):
    if string1[i] in vowels:
        print(f"Vogal: {string1[i]}")
        count += 1
print("Quantidade de vogais na string é: {}".format(count))
# %%
s1 = "Hello World"
for i in range(len(s1)):
    if s1[i] == " ":
        w1 , w2 = s1[:i], s1 [i+1:]
        break
print(w1,w2)
# %%
