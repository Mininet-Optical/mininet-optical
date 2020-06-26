

with open('wdg2.txt', 'r') as f:
    text = f.readlines()

# Add +1 or -1 to the values
# new_text = []
# for line in text:
#     c1 = line[0:1]
#     if c1 == '-':
#         # check for negative number
#         to_add = '-1'
#         new_line = to_add + line[2:]
#     else:
#         to_add = '1'
#         new_line = to_add + line[1:]
#     new_text.append(new_line)

# Increase Nx the original value
x = 3
new_text = []
for line in text:
    print("Line to convert: ", line)
    line_float = float(line[:-3])
    increased_float = line_float * x
    new_line = str(increased_float) + '\n'
    new_text.append(new_line)

with open('wdg2_4.txt', 'w') as f:
    for line in new_text:
        f.write(line)
