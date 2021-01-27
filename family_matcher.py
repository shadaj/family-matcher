import csv
from math import ceil

from mip import Model, xsum, minimize, maximize, BINARY, INTEGER, CONTINUOUS
from util import binary_and, ilp_abs

in_data = open("data.csv")
reader = csv.DictReader(in_data)

junior_mentors = []
senior_mentors = []
all_times = []

for row in reader:
  if row["Which course are you accepting for? (JM)"] == "CS 70" or row["For which course are you a senior mentor?"] == "CS 70":
    times = {}

    if row["Which course are you accepting for? (JM)"] == "CS 70":
      junior_mentors.append({
        "email": row["Berkeley Email"],
        "name": row["Name"],
        "social": int(row["[70] How social would you like your family to be? (JM)"]),
        "times": times
      })

      for key in row.keys():
        if key.startswith("[70] Please mark your family meeting availability (times in PDT) (JM)"):
          extracted_time = key[len("[70] Please mark your family meeting availability (times in PDT) (JM) ["):-1]
          if not extracted_time in all_times:
            all_times.append(extracted_time)
          times[extracted_time] = int(row[key])
    elif row["For which course are you a senior mentor?"] == "CS 70":
      sm_dictionary = {
        "email": row["Berkeley Email"],
        "name": row["Name"],
        "social": int(row["[70] How social would you like your family to be? (SM)"]),
        "times": times
      }

      senior_mentors.append(sm_dictionary)

      for key in row.keys():
        if key.startswith("[70] Please mark your family meeting availability (times in PDT) (SM)"):
          extracted_time = key[len("[70] Please mark your family meeting availability (times in PDT) (SM) ["):-1]
          if not extracted_time in all_times:
            all_times.append(extracted_time)
          times[extracted_time] = int(row[key])

print(junior_mentors)
print(senior_mentors)

model = Model()

sms_per_family = 2
number_of_families = ceil(len(senior_mentors) / sms_per_family)

family_at_time = [[model.add_var(var_type=BINARY) for t in all_times] for p in range(number_of_families)]

jm_in_family = [[model.add_var(var_type=BINARY) for p in range(number_of_families)] for jm in junior_mentors]
jm_at_time = [[model.add_var(var_type=BINARY) for t in all_times] for jm in junior_mentors]

sm_in_family = [[model.add_var(var_type=BINARY) for p in range(number_of_families)] for sm in senior_mentors]
sm_at_time = [[model.add_var(var_type=BINARY) for t in all_times] for sm in senior_mentors]

### Matching Constraints
# each pair is at one time
for pair_i in range(number_of_families):
  model += xsum(
    family_at_time[pair_i][time_i]
    for time_i in range(len(all_times))
  ) == 1

## JM Constraints
# each jm is at one time
for jm_i in range(len(junior_mentors)):
  model += xsum(
    jm_at_time[jm_i][time_i]
    for time_i in range(len(all_times))
  ) == 1

# each jm is in one family
for jm_i in range(len(junior_mentors)):
  model += xsum(
    jm_in_family[jm_i][pair_i]
    for pair_i in range(number_of_families)
  ) == 1

# each jm is at the same time as their family
for jm_i in range(len(junior_mentors)):
  for time_i in range(len(all_times)):
    model += jm_at_time[jm_i][time_i] == xsum(
      binary_and(jm_in_family[jm_i][pair_i], family_at_time[pair_i][time_i], model)
      for pair_i in range(number_of_families)
    )

## SM Constraints
# each sm is at one time
for sm_i in range(len(senior_mentors)):
  model += xsum(
    sm_at_time[sm_i][time_i]
    for time_i in range(len(all_times))
  ) == 1

# each sm is in one family
for sm_i in range(len(senior_mentors)):
  model += xsum(
    sm_in_family[sm_i][pair_i]
    for pair_i in range(number_of_families)
  ) == 1

# each sm is at the same time as their family
for sm_i in range(len(senior_mentors)):
  for time_i in range(len(all_times)):
    model += sm_at_time[sm_i][time_i] == xsum(
      binary_and(sm_in_family[sm_i][pair_i], family_at_time[pair_i][time_i], model)
      for pair_i in range(number_of_families)
    )

# each family has at most N SMs
# this will result in all (but one) families having N SMs because
# number_of_families = ceil(num_sms / N) and N = 2
for family_i in range(number_of_families):
  model += xsum(
    sm_in_family[sm_i][family_i]
    for sm_i in range(len(senior_mentors))
  ) <= sms_per_family

### Optimizing
def section_rating_for_mentor(mentor, get_at_time):
  return xsum(
    get_at_time(t) * mentor["times"][all_times[t]]
    for t in range(len(all_times))
  )

# don't have families that are too big
max_jms_in_family = 6
for family_i in range(number_of_families):
  model += xsum(
    jm_in_family[jm_i][family_i]
    for jm_i in range(len(junior_mentors))
  ) <= max_jms_in_family

worst_allowed_time_rating_sm = 3 # every sm doesn't hate their family time
for sm_i in range(len(senior_mentors)):
  model += section_rating_for_mentor(
    senior_mentors[sm_i],
    lambda time_i: sm_at_time[sm_i][time_i]
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
  section_rating_for_mentor(
    senior_mentors[sm_i],
    lambda time_i: sm_at_time[sm_i][time_i]
  )
  for sm_i in range(len(senior_mentors))
) / len(senior_mentors)

# 0 = bad, 3 = great
average_senior_mentor_rating_goodness = 4 - average_senior_mentor_rating

# note: dividing by sms_per_family won't work well for the odd family out, but we have an even number
# and I'm too lazy to write the logic to precalculate the distribution of uneven SM counts
def average_sm_social_score(family_i):
  return xsum(sm_in_family[sm_i][family_i] * senior_mentors[sm_i]["social"] for sm_i in range(len(senior_mentors))) / sms_per_family

# across all JMs
average_socialness_deviation_jm = xsum(
  xsum(
    ilp_abs(
      jm_in_family[jm_i][sm_pair_i] * junior_mentors[jm_i]["social"]
      - average_sm_social_score(sm_pair_i),
      CONTINUOUS,
      model
    )
    for jm_i in range(len(junior_mentors))
  )
  for sm_pair_i in range(number_of_families)
) / len(junior_mentors)

# across all SMs
average_socialness_deviation_sm = xsum(
  xsum(
    ilp_abs(
      sm_in_family[sm_i][sm_pair_i] * senior_mentors[sm_i]["social"]
      - average_sm_social_score(sm_pair_i),
      CONTINUOUS,
      model
    )
    for sm_i in range(len(senior_mentors))
  )
  for sm_pair_i in range(number_of_families)
) / len(senior_mentors)

# top priority: jm happiness and sm happiness
# then, make socialness match
model.objective = maximize(
  10 * (average_junior_mentor_rating_goodness + average_senior_mentor_rating_goodness)
  - 5 * average_socialness_deviation_jm - 5 * average_socialness_deviation_sm
)

status = model.optimize()
if model.num_solutions > 0:
  print("Junior Mentors: {}".format(len(junior_mentors)))
  print("Senior Mentor Pairs: {}".format(number_of_families))
  for family_i in range(number_of_families):
    jms = []
    for jm_i in range(len(junior_mentors)):
      if jm_in_family[jm_i][family_i].x >= 0.99:
        jms.append(junior_mentors[jm_i])

    sms = []
    for sm_i in range(len(senior_mentors)):
      if sm_in_family[sm_i][family_i].x >= 0.99:
        sms.append(senior_mentors[sm_i])

    time = None
    for time_i in range(len(all_times)):
      if family_at_time[family_i][time_i].x >= 0.99:
        time = all_times[time_i]

    print()
    print(time)
    print(", ".join(["{} (time: {}, social: {})".format(sm["name"], sm["times"][time], sm["social"]) for sm in sms]))
    print(", ".join(["{} (time: {}, social: {})".format(jm["name"], jm["times"][time], jm["social"]) for jm in jms]))

  print("------------------------")

  for family_i in range(number_of_families):
    jms = []
    for jm_i in range(len(junior_mentors)):
      if jm_in_family[jm_i][family_i].x >= 0.99:
        jms.append(junior_mentors[jm_i])

    sms = []
    for sm_i in range(len(senior_mentors)):
      if sm_in_family[sm_i][family_i].x >= 0.99:
        sms.append(senior_mentors[sm_i])

    time = None
    for time_i in range(len(all_times)):
      if family_at_time[family_i][time_i].x >= 0.99:
        time = all_times[time_i]

    family_name = "/".join(sm["name"] for sm in sms)
    meeting_day = time.split()[0]
    meeting_time = time.split()[1]
    sm_names = [sm["name"] for sm in sms]
    jm_names = [jm["name"] for jm in jms]

    print(";".join([family_name, meeting_day, meeting_time, *sm_names, *jm_names]))
