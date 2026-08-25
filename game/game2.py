import random, sys
letters = list(r"abcdefghijklmnopqretuvwxyz1234567890:<>?{}_+|)(*&%^$#@!,/.';][\-=])")
# print 2 random letters and clear screen
while True:
    print(random.choice(letters)+random.choice(letters)+random.choice(letters)+random.choice(letters)+random.choice(letters)+random.choice(letters)+random.choice(letters))
    #clear screen
    sys.stdout.write("\033[H\033[J")
# minecraft