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

not_teaching = [] # names of people who aren't teaching
multi_sections = []

mode = "88"

for row in reader:
  if mode == "61b-family":
    if row["Which course are you accepting for? (JM)"] == "CS 61b":
      junior_mentors += 1

      times = {}
      mentors.append({
        "email": row["Berkeley Email"],
        "name": row["Name"],
        "times": times
      })

      for key in row.keys():
        if key.startswith("[61B] Please mark your family meeting availability"):
          extracted_time = key[len("[61B] Please mark your family meeting availability ["):-1]
          if not extracted_time in all_times:
            all_times.append(extracted_time)
          times[extracted_time] = int(row[key])
  elif mode == "88-family":
    if row["Which course are you accepting for? (JM)"] == "CS 88":
      junior_mentors += 1

      times = {}
      mentors.append({
        "email": row["Berkeley Email"],
        "name": row["Name"],
        "times": times
      })

      for key in row.keys():
        if key.startswith("[88] Please mark your family meeting availability"):
          extracted_time = key[len("[88] Please mark your family meeting availability ["):-1]
          if not extracted_time in all_times:
            all_times.append(extracted_time)
          times[extracted_time] = int(row[key])
  elif mode == "70":
    if (not row["Name"] in not_teaching):
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
          if key.startswith("[70] Select the times you would like to hold section (times in PDT)"):
            extracted_time = key[len("[70] Select the times you would like to hold section (times in PDT) ["):-1]
            if not extracted_time in all_times:
              all_times.append(extracted_time)
            times[extracted_time] = int(row[key])
  elif mode == "61b":
    if (not row["Name"] in not_teaching):
      if row["Which course are you accepting for? (JM)"] == "CS 61b" or row["Which course are you accepting for? (AM)"] == "CS 61b" or row["For which course are you a senior mentor?"] == "CS 61b":
        if row["Which course are you accepting for? (JM)"] == "CS 61b":
          junior_mentors += 1
        elif row["Which course are you accepting for? (AM)"] == "CS 61b":
          associate_mentors += 1
        elif row["For which course are you a senior mentor?"] == "CS 61b":
          senior_mentors += 1

        times = {}
        section_count = row["[61b] How many sections would you like to teach? (Only one section is required)"]
        mentors.append({
          "email": row["Berkeley Email"],
          "name": row["Name"],
          "times": times
        })

        if section_count == "Two Sections":
          mentors.append({
            "email": row["Berkeley Email"],
            "name": row["Name"] + " (second section)",
            "times": times
          })

          multi_sections.append(row["Berkeley Email"])

        for key in row.keys():
          if key.startswith("[61b] Select all times you'd like to hold section (Times in PDT) "):
            extracted_time = key[len("[61b] Select all times you'd like to hold section (Times in PDT) ["):-1]
            if not extracted_time == "Other (specify below)":
              if not extracted_time in all_times:
                all_times.append(extracted_time)
              if len(row[key]) == 0:
                times[extracted_time] = 3
              else:
                selected = list(map(lambda x: {
                  "Can't Do": 5,
                  "Low Preference": 4,
                  "Medium Preference": 3,
                  "High Preference": 2,
                  "Very High Preference": 1
                }[x], row[key].split(";")))
                times[extracted_time] = float(sum(selected)) / len(selected)
  elif mode == "88":
    if (not row["Name"] in not_teaching):
      if row["Which course are you accepting for? (JM)"] == "CS 88" or row["Which course are you accepting for? (AM)"] == "CS 88" or row["For which course are you a senior mentor?"] == "CS 88":
        if row["Which course are you accepting for? (JM)"] == "CS 88":
          junior_mentors += 1
        elif row["Which course are you accepting for? (AM)"] == "CS 88":
          associate_mentors += 1
        elif row["For which course are you a senior mentor?"] == "CS 88":
          senior_mentors += 1

        times = {}
        mentors.append({
          "email": row["Berkeley Email"],
          "name": row["Name"],
          "times": times
        })

        for key in row.keys():
          if key.startswith("[88] What day would you like to teach section? "):
            extracted_time = key[len("[88] What day would you like to teach section? ["):-1]
            if not extracted_time == "Other (specify below)":
              if not extracted_time in all_times:
                all_times.append(extracted_time)
              if len(row[key]) == 0:
                times[extracted_time] = 3
              else:
                selected = list(map(lambda x: {
                  "Can't Do": 5,
                  "Low Preference": 4,
                  "Medium Preference": 3,
                  "High Preference": 2,
                  "Very High Preference": 1
                }[x], row[key].split(";")))
                times[extracted_time] = float(sum(selected)) / len(selected)
  elif mode == "61c":
    if (not row["Name"] in not_teaching):
      if row["Which course are you accepting for? (JM)"] == "CS 61c" or row["Which course are you accepting for? (AM)"] == "CS 61c" or row["For which course are you a senior mentor?"] == "CS 61c":
        if row["Which course are you accepting for? (JM)"] == "CS 61c":
          junior_mentors += 1
        elif row["Which course are you accepting for? (AM)"] == "CS 61c":
          associate_mentors += 1
        elif row["For which course are you a senior mentor?"] == "CS 61c":
          senior_mentors += 1

        times = {}
        section_count = row["How many sections would you like to teach? (Only one section is required for CSM, 1hr a week)"]
        if not section_count == "No Sections (must be a SM & TA/tutor on 61C course staff)":
          mentors.append({
            "email": row["Berkeley Email"],
            "name": row["Name"],
            "times": times
          })

          if section_count == "Two Sections":
            mentors.append({
              "email": row["Berkeley Email"],
              "name": row["Name"] + " (second section)",
              "times": times
            })

          for key in row.keys():
            if key.startswith("[61C] Select the times you would like to hold section (times in PDT)"):
              extracted_time = key[len("[61C] Select the times you would like to hold section (times in PDT) ["):-1]
              if not extracted_time == "Other":
                if not extracted_time in all_times:
                  all_times.append(extracted_time)
                if len(row[key]) == 0:
                  times[extracted_time] = 3
                else:
                  selected = list(map(int, row[key].split(";")))
                  times[extracted_time] = float(sum(selected)) / len(selected)

if mode == "61b-family":
  all_times.append("Tuesday 5PM-6PM PT") # two families at same side

average_sections = float(len(mentors)) / len(all_times)

model = Model()
teaching_section = [[model.add_var(var_type=BINARY) for t in all_times] for m in mentors]

for m in range(len(mentors)):
  if mentors[m]["email"] in multi_sections and (not mentors[m]["name"].endswith("(second section)")):
    index_of_other = [i for i in range(len(mentors)) if mentors[i]["email"] == mentors[m]["email"] and i != m][0]
    for t in range(len(all_times)):
      model += (teaching_section[m][t] + teaching_section[index_of_other][t]) <= 1

# each mentor teaches exactly one section
for m in range(len(mentors)):
  model += xsum(teaching_section[m][t] for t in range(len(all_times))) == 1

def section_rating_for_mentor(m):
  return xsum(
    teaching_section[m][t] * mentors[m]["times"][all_times[t]]
    for t in range(len(all_times))
  )

worst_allowed_section_rating = {
  "70": 4,
  "61b": 4,
  "88": 5,
  "61b-family": 4,
  "88-family": 4,
  "61c": 4,
}[mode] # everyone doesn't hate their section
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
max_section_score = {
  "70": 4,
  "61b": 5,
  "88": 5,
  "61b-family": 4,
  "88-family": 4,
  "61c": 5,
}[mode]
average_mentor_rating_goodness = max_section_score - average_mentor_rating

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
    if mentors[m]["times"][section] == 5.0:
      print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
      print(mentors[m]["email"])
  
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
        times.append("Tuesday")
        times.append(time)
        times.append("Thursday")
        times.append(time)
      else:
        times.append("Monday")
        times.append(time)
        times.append("Wednesday")
        times.append(time)
    elif mode == "61b" or mode == "88":
      time = section.replace(" AM", ":00 AM").replace(" PM", ":00 PM")
      times.append(section.split()[0])
      times.append(time)
    elif mode == "61c":
      time = section.split()[1].replace("am", ":00 AM").replace("pm", ":00 PM")
      times.append(section.split()[0])
      times.append(time)
    print(";".join([mentors[m]["email"], *times]))
