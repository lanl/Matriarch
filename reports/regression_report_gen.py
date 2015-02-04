# Copyright (c) 2014, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright 2014. Los Alamos National Security, LLC. This software was 
# produced under U.S. Government contract DE-AC52-06NA25396 for Los Alamos
# National Laboratory (LANL), which is operated by Los Alamos National 
# Security, LLC for the U.S. Department of Energy. The U.S. Government has 
# rights to use, reproduce, and distribute this software.  NEITHER THE 
# GOVERNMENT NOR LOS ALAMOS NATIONAL SECURITY, LLC MAKES ANY WARRANTY, EXPRESS
# OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If 
# software is modified to produce derivative works, such modified software 
# should be clearly marked, so as not to confuse it with the version available
# from LANL.
# 
# Additionally, redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
# · Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# · Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# · Neither the name of Los Alamos National Security, LLC, Los Alamos National
#   Laboratory, LANL, the U.S. Government, nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY LOS ALAMOS NATIONAL SECURITY, LLC AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOS ALAMOS NATIONAL 
# SECURITY, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function
from __future__ import division
from future_builtins import map, filter

import json
import urllib
import sys
import datetime
from scipy import stats
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

template = "sedov"
tag = "reg_test"
matriarch = "http://localhost:8081"

date_format = "%x"
group_name = "HPC-5"

revisions_back = 7

PERCENT = "\\%"

req = urllib.urlopen(matriarch + "/api/data/" + template)
j = json.loads(req.read())

revs = {}

for i in j:
    if i['regression_tag'] != tag:
        continue


    if i['offset'] not in revs:
        revs[i['offset']] = []

    revs[i['offset']].append(i)


relevant_revs = sorted(revs.keys(), reverse=True)[:revisions_back]
relevant_points = list(map(lambda x: datetime.datetime.fromtimestamp(int(x)), relevant_revs))


durations = list(map(lambda x: [y['DURATION'] for y in revs[x]], relevant_revs))


def compare(durations, a, b):
    conf = 1.0 - stats.ttest_ind(durations[a], durations[b])[1]
    conf = "{:.1%}".format(conf).replace("%", PERCENT)
    change = (np.mean(durations[b]) - np.mean(durations[a])) / np.mean(durations[a])
    change = "{:.1%}".format(change).replace("%", PERCENT)
    return (change, conf)
    

def wrap_num(n):
    return "$" + str(n) + "$"

def gen_statement(durations, dates, a, b):
    nums = compare(durations, a, b)
    return ("Between %s and %s (a period of %s %s), performance appears to have %s by %s with %s confidence." 
            % (dates[b].strftime(date_format), dates[a].strftime(date_format), 
               wrap_num(int(round(abs(dates[b] - dates[a]).total_seconds() / 86400))), "days",
               "degraded" if nums[0][0] == "-" else "improved", wrap_num(nums[0]),
               wrap_num(nums[1])))

def interpret_conf(durations, a, b):
    nums = compare(durations, a, b)
    perc = 1.0 - (float(nums[1][0:nums[1].find(".")]) / 100.0)

    if perc > 0.1:
        return "This change is not statistically significant."
    elif perc > 0.05:
        return "This change may be statistically significant."
    elif perc > 0.01:
        return "This change is statistically significant."
    else:
        return "This change is very statistically significant."


def gen_r_val(dates, durations):
    y = list(map(np.mean, durations))
    R = np.corrcoef(dates, y)[0][1]
    return ("Overall, the mean performance has an $R$ value of %s. This means that there is a %s %s correlation between time and performance. The code seems to be \\textbf{getting %s} over the examined time period. Approximately %s of the change in performance is explained by a linear model." %
            (wrap_num(round(R, 2)), "weak" if abs(R) < 0.5 else "strong", 
             "positive" if R < 0.0 else "negative", 
             "faster" if R < 0.0 else "slower",
            wrap_num("{:.1%}".format(R**2).replace("%", PERCENT))))


def gen_tbl_align(revisions):
    return "|".join(("l" for i in range(revisions)))


def gen_cell(durations, a, b):
    if a == b:
        return ""

    nums = compare(durations, a, b)
    perc = 1.0 - (float(nums[1][0:nums[1].find(".")]) / 100.0)

    if perc > 0.1:
        color = 0
    elif perc > 0.05:
        color = 25
    elif perc > 0.01:
        color = 66
    else:
        color = 100


    return "\\cellcolor{red!%s} %s" % (color, nums[0])

def gen_tbl(dates, durations):
    toR = "\\hline \n  & "
    toR += " & ".join([i.strftime("%x") for i in dates])
    toR += " \\\\"
    toR += "\n\\hline \n"
    

    for i in range(len(dates)):
        toR += dates[i].strftime("%x") + " & "
        toR += " & ".join([gen_cell(durations, i, j) for j in range(len(dates))])
        toR += " \\\\ \n"
        toR += "\hline \n"

    return toR


def generate_plot(x, y):
    y_err = list(map(np.ptp, y))
    y = list(map(np.mean, y))
    
    plt.errorbar(x, y, yerr=y_err, xerr=0)
    plt.xticks(x, list(map(lambda x: datetime.datetime.fromtimestamp(x).strftime("%x"), x)))
    plt.xlabel("Date")
    plt.ylabel("Duration (seconds)")
    plt.title("Performance over Time")
    plt.savefig("plot.png", bbox_inches='tight')



generate_plot(relevant_revs, durations)

print('\\documentclass[11pt]{article}')
print('\\usepackage{graphicx}')
print('\\usepackage[table]{xcolor}')
print('\\title{', "Matriarch Regression Analysis Report (%s)" % template, "}")
print('\\author{', "Generated automatically by Matriarch", '\\\\', group_name, "}")
print("\\date{%s}" % relevant_points[0].strftime("%x"))

print('\\begin{document}')
print('\\maketitle')

print('\\begin{abstract}')
print("Matriarch measured the change in job duration for the %s template at %d points between %s and %s." 
      % (template, revisions_back, relevant_points[-1].strftime("%x"), relevant_points[0].strftime("%x")))
print(gen_statement(durations, relevant_points, 0, 1))
print(interpret_conf(durations, 0, 1))


print('\\end{abstract}')

print("\\section{Overview}")

print(gen_r_val(relevant_revs, durations))
print()

print("The most recent test was performed on %s. The mean runtime was %s seconds, with a standard deviation of %s seconds. The previous test had mean runtime %s seconds with standard deviation %s seconds." % (relevant_points[0].strftime("%x"), wrap_num(np.mean(durations[0])), wrap_num(np.std(durations[0])), wrap_num(np.mean(durations[1])), wrap_num(np.std(durations[1]))))
print()

print("Figure~\\ref{fig:pot} shows a graph of changes in performance over time. Comparisons between the most recent test and the past %(cnt)s tests is given in section~\\ref{sec:bt}. Table~\\ref{tbl:comp} shows each of the %(cnt)s tests compared to each other." % {'cnt':wrap_num(revisions_back)})
print()

print("\\begin{figure}")
print("\\centering")
print("\\includegraphics[width=\\columnwidth]{plot.png}")
print("\\caption{A plot of performance over time, including error}")
print("\\label{fig:pot}")
print("\\end{figure}")

print("\\begin{table}")
print("\\centering")
print("\\resizebox{\\columnwidth}{!}{%")
print("\\begin{tabular}{|%s|}" % (gen_tbl_align(revisions_back + 1)))
print(gen_tbl(relevant_points, durations))
print("\\end{tabular}%")
print("}")
print("\\label{tbl:comp}")
print("\\caption{Tests compared to each other. Darker cells represent more significant results.}")
print("\\end{table}")



print('\\section{Back-testing}')
print('\\label{sec:bt}')
print("\\begin{itemize}")
for i in range(1, revisions_back):
    print("\\item", gen_statement(durations, relevant_points, 0, i))
    print(interpret_conf(durations, 0, i))
    print()
print("\\end{itemize}")

print("\\section{Notice}")
print("This report was generated by Matriarch, a framework for automated performance analysis initially developed at Los Alamos National Laboratory. Any rights to this report, including but not limited to the right to redistribute, modify, or remix this document, belong to the individual who generated the report. Regardless of Matriarch's license, all rights of this generated report are reserved.")
print()

print("If this report was generated at a DOE facility, note that its content may require the same protections as the code analyzed. If the analyzed code is export controlled or OYO, this report \\emph{may} be exempt from public release under the Freedom of Information Act (5 U.S.C. 552), exemption number and category: Exemption 3 - Statutory Exemption. A Department of Energy Review may be required before public release.")

print("\\end{document}")

