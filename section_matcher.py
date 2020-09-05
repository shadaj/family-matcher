import csv

from mip import Model, xsum, minimize, maximize, BINARY, INTEGER, CONTINUOUS
from util import ilp_abs

in_data = open("data.csv")
reader = csv.DictReader(in_data)

junior_mentors = 0
associate_mentors = 0
senior_mentors = 0

mentors = []
all_times = []

mode = "70"

for row in reader:
  if mode == "61b-family":
    if row["Which course are you accepting for? (JM)"] == "CS 61b":
      if row["Which course are you accepting for? (JM)"] == "CS 61b":
        junior_mentors += 1

      times = {}
      mentors.append({
        "email": row["Berkeley Email"],
        "name": row["Name"],
        "times": times
      })

      for key in row.keys():
        if key.startswith("Please mark your family meeting availability (61B)"):
          extracted_time = key[len("Please mark your family meeting availability (61B) ["):-1]
          if not extracted_time in all_times:
            all_times.append(extracted_time)
          times[extracted_time] = int(row[key])
  elif mode == "70":
    if (row["Name"] != "Angela Jiang"): # Angela isn't teaching
      if row["Which course are you accepting for? (JM)"] == "CS 70" or row["Which course are you accepting for? (AM)"] == "CS 70" or row["For which course are you a senior mentor?"] == "CS 70":
        if row["Which course are you accepting for? (JM)"] == "CS 70":
          junior_mentors += 1
        elif row["Which course are you accepting for? (AM)"] == "CS 70":
          associate_mentors += 1
        elif row["For which course are you a senior mentor?"] == "CS 70":
          senior_mentors += 1

        times = {}
        mentors.append({
          "email": row["Berkeley Email"],
          "name": row["Name"],
          "times": times
        })

        for key in row.keys():
          if key.startswith("Select the times you would like to hold section (times in PDT)"):
            extracted_time = key[len("Select the times you would like to hold section (times in PDT) ["):-1]
            if not extracted_time in all_times:
              all_times.append(extracted_time)
            times[extracted_time] = int(row[key])

if mode == "61b-family":
  all_times.append("Monday 	11:00 AM PDT") # two families at same side

average_sections = float(len(mentors)) / len(all_times)

model = Model()
teaching_section = [[model.add_var(var_type=BINARY) for t in all_times] for m in mentors]

# each mentor teaches exactly one section
for m in range(len(mentors)):
  model += xsum(teaching_section[m][t] for t in range(len(all_times))) == 1

def section_rating_for_mentor(m):
  return xsum(
    teaching_section[m][t] * mentors[m]["times"][all_times[t]]
    for t in range(len(all_times))
  )

worst_allowed_section_rating = 3 # everyone doesn't hate their section
# each mentor doesn't hate their section
for m in range(len(mentors)):
  model += section_rating_for_mentor(m) <= worst_allowed_section_rating

def deviation_from_average_sections(time_index):
  return ilp_abs(
    xsum(teaching_section[m][time_index] for m in range(len(mentors))) - average_sections,
    CONTINUOUS,
    model
  )

average_mentor_rating = xsum(
  section_rating_for_mentor(m)
  for m in range(len(mentors))
) / len(mentors)

# 0 = bad, 3 = great
average_mentor_rating_goodness = 4 - average_mentor_rating

average_section_deviation = xsum(
  deviation_from_average_sections(t) for t in range(len(all_times))
) / len(mentors)

# section spread is way more important than average happiness
model.objective = maximize(
  average_mentor_rating_goodness - 1000 * average_section_deviation
)

status = model.optimize()
if model.num_solutions > 0:
  print("Junior Mentors: {}".format(junior_mentors))
  print("Associate Mentors: {}".format(associate_mentors))

  print("Senior Mentors: {}".format(senior_mentors))
  for m in range(len(mentors)):
    section = None
    for time_index in range(len(all_times)):
      if teaching_section[m][time_index].x >= 0.99:
        section = all_times[time_index]
    print("{} - {} (section rating: {})".format(mentors[m]["name"], section, mentors[m]["times"][section]))
  
  for t in range(len(all_times)):
    print(all_times[t] + ": " + ", ".join([ mentors[m]["name"] for m in range(len(mentors)) if teaching_section[m][t].x == 1.0 ]))

  print("------------------------")

  for m in range(len(mentors)):
    section = None
    for time_index in range(len(all_times)):
      if teaching_section[m][time_index].x >= 0.99:
        section = all_times[time_index]
    
    times = []
    if mode == "70":
      time = section.split()[3].replace("AM", ":00 AM").replace("PM", ":00 PM")
      if section.startswith("Tue / Thurs"):
        times.append("Tuesday [{}]".format(time))
        times.append("Thursday [{}]".format(time))
      else:
        times.append("Monday [{}]".format(time))
        times.append("Wednesday [{}]".format(time))
    print(";".join([mentors[m]["email"], *times]))
