#%%
#Given two vectors {A} and {B} calculate the scalar (dot) product
n = int(input("Number of elements = "))
a = [0] * n
b = [0] * n
for i in range(n):
    a[i] = float(input("a[" + str(i) + "]="))
for i in range(n):
    b[i] = float(input("b[" + str(i) + "]="))

scalarprod=0.0
for i in range(n):
    scalarprod += a[i] * b[i]
print("Scalar product =", scalarprod)


# %%
#Calculate the sum of two matrices [A] and [B]

n = int(input("Number of lines = "))
m = int(input("Number of columns = "))
a = [[0] * m for i in range(n)]
b = [[0] * m for i in range(n)]
c = [[0] * m for i in range (n)]

for i in range(n):
    for j in range(m):
        a[i][j] = float(input("a[" + str(i) + "][" + str(j) + "]="))
for i in range(n):
    for j in range(m):
        b[i][j] = float(input("b[" + str(i) + "][" + str(j) + "]="))
for i in range(n):
    for j in range(m):
        c[i][j] = a[i][j] + b[i][j]
for i in range(n):
    print(c[i])      
# %% Calculate the maximum value of a matrix and its position (row, columm)
columns = int(input("Insert the number of columns: "))
rows = int(input("Insert the number of rows: "))

a_matrix = [[0]*columns for i in range(rows)] 

for i in range(rows):
    for j in range(columns):
        a_matrix[i][j] = float(input("a[" + str(i) + "][" + str(j) + "]="))

max_total = -99999999999999
for i in range(rows):
    max_row = max(a_matrix[i])
    if max_row > max_total:
        max_total = max_row


print("Maximum value:", max_total)



# %%
