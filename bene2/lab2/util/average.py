data = [float(line[:-1]) for line in open("queue_delay.txt", "r")]
print float(sum(data)) / len(data)
