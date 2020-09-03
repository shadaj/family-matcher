import csv

from mip import Model, xsum, minimize, maximize, BINARY, INTEGER, CONTINUOUS
from util import binary_and

in_data = open("data.csv")
reader = csv.DictReader(in_data)

junior_mentors = []
senior_mentors = []
sm_by_email = {}
sm_pairs = []
all_times = []

for row in reader:
  if row["Which course are you accepting for? (JM)"] == "CS 70" or row["For which course are you a senior mentor?"] == "CS 70":
    times = {}
    
    if row["Which course are you accepting for? (JM)"] == "CS 70":
      junior_mentors.append({
        "email": row["Berkeley Email"],
        "name": row["Name"],
        "times": times
      })

      for key in row.keys():
        if key.startswith("Please mark your family meeting availability (times in PDT) (JM)"):
          extracted_time = key[len("Please mark your family meeting availability (times in PDT) (JM) ["):-1]
          if not extracted_time in all_times:
            all_times.append(extracted_time)
          times[extracted_time] = int(row[key])
    elif row["For which course are you a senior mentor?"] == "CS 70":
      sm_dictionary = {
        "email": row["Berkeley Email"],
        "name": row["Name"],
        "times": times
      }

      senior_mentors.append(sm_dictionary)

      if not sm_dictionary["email"] in sm_by_email:
        sm_by_email[sm_dictionary["email"]] = sm_dictionary

      if row["What is your co-SM's email address?"] in sm_by_email:
        sm_pairs.append([
          sm_dictionary,
          sm_by_email[row["What is your co-SM's email address?"]]
        ])

        del sm_by_email[sm_dictionary["email"]]
        del sm_by_email[row["What is your co-SM's email address?"]]

      for key in row.keys():
        if key.startswith("Please mark your family meeting availability (times in PDT) (SM)"):
          extracted_time = key[len("Please mark your family meeting availability (times in PDT) (SM) ["):-1]
          if not extracted_time in all_times:
            all_times.append(extracted_time)
          times[extracted_time] = int(row[key])

for remaining in sm_by_email.values():
  sm_pairs.append([remaining])

model = Model()

pair_at_time = [[model.add_var(var_type=BINARY) for t in all_times] for p in sm_pairs]
jm_in_pair = [[model.add_var(var_type=BINARY) for p in sm_pairs] for jm in junior_mentors]
jm_at_time = [[model.add_var(var_type=BINARY) for t in all_times] for jm in junior_mentors]

# each pair is at one time
for pair_i in range(len(sm_pairs)):
  model += xsum(
    pair_at_time[pair_i][time_i]
    for time_i in range(len(all_times))
  ) == 1

# each jm is at one time
for jm_i in range(len(junior_mentors)):
  model += xsum(
    jm_at_time[jm_i][time_i]
    for time_i in range(len(all_times))
  ) == 1

# each jm is in one pair
for jm_i in range(len(junior_mentors)):
  model += xsum(
    jm_in_pair[jm_i][pair_i]
    for pair_i in range(len(sm_pairs))
  ) == 1

# each jm is at the same time as their sm pair
for jm_i in range(len(junior_mentors)):
  for time_i in range(len(all_times)):
    model += jm_at_time[jm_i][time_i] == xsum(
      binary_and(jm_in_pair[jm_i][pair_i], pair_at_time[pair_i][time_i], model)
      for pair_i in range(len(sm_pairs))
    )

def section_rating_for_mentor(mentor, get_at_time):
  return xsum(
    get_at_time(t) * mentor["times"][all_times[t]]
    for t in range(len(all_times))
  )

# don't have families that are too big
max_jms_in_family = 6
for sm_pair_i in range(len(sm_pairs)):
  model += xsum(
    jm_in_pair[jm_i][sm_pair_i]
    for jm_i in range(len(junior_mentors))
  ) <= max_jms_in_family

worst_allowed_time_rating_sm = 3 # every sm doesn't hate their family time
for sm_pair_i in range(len(sm_pairs)):
  for sm in sm_pairs[sm_pair_i]:
    model += section_rating_for_mentor(
      sm,
      lambda time_i: pair_at_time[sm_pair_i][time_i]
    ) <= worst_allowed_time_rating_sm

worst_allowed_time_rating_jm = 3 # every jm doesn't hate their family time
for jm_i in range(len(junior_mentors)):
  model += section_rating_for_mentor(
    junior_mentors[jm_i],
    lambda time_i: jm_at_time[jm_i][time_i]
  ) <= worst_allowed_time_rating_jm

average_junior_mentor_rating = xsum(
  section_rating_for_mentor(
    junior_mentors[jm_i],
    lambda time_i: jm_at_time[jm_i][time_i]
  )
  for jm_i in range(len(junior_mentors))
) / len(junior_mentors)

# 0 = bad, 3 = great
average_junior_mentor_rating_goodness = 4 - average_junior_mentor_rating

average_senior_mentor_rating = xsum(
  # every family has equal weight regardless of SM submissions
  xsum(
    section_rating_for_mentor(
      sm,
      lambda time_i: pair_at_time[sm_pair_i][time_i]
    )
    for sm in sm_pairs[sm_pair_i]
  ) / len(sm_pairs[sm_pair_i])
  for sm_pair_i in range(len(sm_pairs))
) / len(sm_pairs)

# 0 = bad, 3 = great
average_senior_mentor_rating_goodness = 4 - average_senior_mentor_rating

# top priority: jm happiness and sm happiness
model.objective = maximize(
  average_junior_mentor_rating_goodness + average_senior_mentor_rating_goodness
)

status = model.optimize()
if model.num_solutions > 0:
  print("Junior Mentors: {}".format(len(junior_mentors)))
  print("Senior Mentor Pairs: {}".format(len(sm_pairs)))
  for sm_i in range(len(sm_pairs)):
    jms = []
    for jm_i in range(len(junior_mentors)):
      if jm_in_pair[jm_i][sm_i].x >= 0.99:
        jms.append(junior_mentors[jm_i])
    
    time = None
    for time_i in range(len(all_times)):
      if pair_at_time[sm_i][time_i].x >= 0.99:
        time = all_times[time_i]

    print()
    print(time)
    print(", ".join(["{} (time rating: {})".format(sm["name"], sm["times"][time]) for sm in sm_pairs[sm_i]]))
    print(", ".join(["{} (time rating: {})".format(jm["name"], jm["times"][time]) for jm in jms]))