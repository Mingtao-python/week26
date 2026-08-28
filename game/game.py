'''test how long does python need to count to 1 billion and test how long it take to make _=0'''
import time

start = time.time()
_=0
end = time.time()
answer = end - start
print(f"time taken: {end - start} seconds")
start = time.time()
for i in range(1000000000):
    _ = 0
end = time.time()

print(f"Time taken: {end - start - 1000000000*answer} seconds")