# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

import fileinput
import re
import sys


def parse_gstat_output() -> (list, list):
    tables = []  # (table_name, table_size)
    indices = []  # (table_name, index_name, index_size, depth)
    cur_table = ""
    cur_page_count = 0
    cur_index = ""
    cur_index_leaf_count = 0
    cur_index_depth = ""
    cur_page_size = 0
    cur_section = ""

    for line in fileinput.input():
        # skip empty lines
        s = line.replace("\n", "")
        if len(s) == 0:
            continue
        # detecting section change
        if s.startswith("Database header page"):
            cur_section = "header"
            continue
        if s.startswith("Analyzing database pages"):
            cur_section = "tables"
            continue
        # getting data from header information section
        if cur_section == "header":
            m = re.match(r"^\s*Page size\s.(\d*).*", s)
            if m is not None:
                cur_page_size = int(m.group(1))
                # print("Found page size:", cur_page_size)
                continue
        # getting data from tables/indexes section
        if cur_section == "tables":
            if s[0] not in " \t":  # new table starts
                if cur_table != "":
                    if cur_index != "":
                        indices.append(
                            (
                                cur_table,
                                cur_index,
                                cur_index_leaf_count,
                                cur_index_depth,
                            )
                        )
                        cur_index = ""
                        cur_index_leaf_count = 0
                        cur_index_depth = 0
                    tables.append((cur_table, cur_page_count))
                cur_table = s
                cur_page_count = 0
                continue
            else:  # inside current table
                m = re.match(r"^\s*Data pages: (\d*).*", s)
                if m is not None:
                    cur_page_count = int(m.group(1))
                    continue
                m = re.match(r"^\s*Index (.*)$", s)
                if m is not None:
                    if cur_index != "":
                        indices.append(
                            (
                                cur_table,
                                cur_index,
                                cur_index_leaf_count,
                                cur_index_depth,
                            )
                        )
                    cur_index = m.group(1).strip()
                    cur_index_leaf_count = 0
                    cur_index_depth = 0
                    continue
                m = re.match(r"^\s*Depth: (\d*).*leaf buckets: (\d*).*", s)
                if m is not None:
                    cur_index_depth = int(m.group(1))
                    cur_index_leaf_count = int(m.group(2))
                    continue
    # prepare result data
    # [(table_name, table_size_bytes, table_size_megabytes),  ]
    result_tables = []
    for (tabname, tabsize) in tables:
        tabsize_bytes = tabsize * cur_page_size
        tabsize_megabytes = round(tabsize_bytes / 1024 / 1024, 2)
        result_tables.append((tabname, tabsize_bytes, tabsize_megabytes))
    result_tables.sort(key=lambda tup_table: tup_table[1], reverse=True)

    # [(table_name,  index_name, index_size_bytes, index_size_megabytes, index_depth),]
    result_indices = []
    for (tabname, indexname, indexsize, indexdepth) in indices:
        indexsize_bytes = indexsize * cur_page_size
        indexsize_megabytes = round(indexsize_bytes / 1024 / 1024, 2)
        result_indices.append(
            (tabname, indexname, indexsize_bytes, indexsize_megabytes, indexdepth)
        )
    result_indices.sort(key=lambda tup_index: tup_index[2], reverse=True)

    return (result_tables, result_indices)


def print_horizontal_line(len: int, ch: str = "-"):
    print(ch * len)


def print_tables_row(val1: str, val2: str, val3: str, len1: int, len2: int, len3: int):
    s = f"| {val1:<{len1}} | {val2:>{len2}} | {val3:>{len3}} |"
    print(s)


def print_indices_row(
    val1: str,
    val2: str,
    val3: str,
    val4: str,
    val5: str,
    len1: int,
    len2: int,
    len3: int,
    len4: int,
    len5: int,
):
    s = (
        f"| "
        f"{val1:<{len1}} | "
        f"{val2:<{len2}} | "
        f"{val3:>{len3}} | "
        f"{val4:>{len4}} | "
        f"{val5:>{len5}} |"
    )
    print(s)


def pretty_int(val: int) -> int:
    return "{0:,}".format(val).replace(",", " ")


def pretty_float(val: float, prec: int) -> str:
    return "{0:,.{1}f}".format(val, prec).replace(",", " ")


def print_tables_info(tables: list):
    # determining column widths and line width
    label1 = "TABLE NAME"
    label2 = "SIZE [B]"
    label3 = "SIZE [MB]"

    len1 = len(label1)
    len2 = len(label2)
    len3 = len(label3)

    for tab in tables:
        len1 = max(len1, len(tab[0].strip()))
        len2 = max(len2, len(pretty_int(tab[1])))
        len3 = max(len3, len(pretty_float(tab[2], 2)))

    line_width = 2 + len1 + 3 + len2 + 3 + len3 + 2

    # printing data
    print_horizontal_line(line_width)
    print_tables_row(label1, label2, label3, len1, len2, len3)
    print_horizontal_line(line_width)
    for tup in tables:
        val1 = tup[0].strip()
        val2 = pretty_int(tup[1])
        val3 = pretty_float(tup[2], 2)
        print_tables_row(val1, val2, val3, len1, len2, len3)
    print_horizontal_line(line_width)


def print_indices_info(indices: list):
    # determining column widths and line width
    label1 = "INDEX NAME"
    label2 = "TABLE NAME"
    label3 = "SIZE [B]"
    label4 = "SIZE [MB]"
    label5 = "DEPTH"

    len1 = len(label1)
    len2 = len(label2)
    len3 = len(label3)
    len4 = len(label4)
    len5 = len(label5)

    for idx in indices:
        len1 = max(len1, len(idx[0].strip()))
        len2 = max(len2, len(idx[1].strip()))
        len3 = max(len3, len(pretty_int(idx[2])))
        len4 = max(len4, len(pretty_float(idx[3], 2)))
        len5 = max(len5, len(pretty_int(idx[4])))

    line_width = 2 + len1 + 3 + len2 + 3 + len3 + 3 + len4 + 3 + len5 + 2

    # printing data
    print_horizontal_line(line_width)
    print_indices_row(
        label1, label2, label3, label4, label5, len1, len2, len3, len4, len5
    )
    print_horizontal_line(line_width)
    for tup in indices:
        val1 = tup[0].strip()
        val2 = tup[1].strip()
        val3 = pretty_int(tup[2])
        val4 = pretty_float(tup[3], 2)
        val5 = pretty_int(tup[4])
        print_indices_row(val1, val2, val3, val4, val5, len1, len2, len3, len4, len5)
    print_horizontal_line(line_width)


def print_summary(tables: list, indices: list):
    tables_total_bytes = 0
    tables_total_megabytes = 0.0
    for tab in tables:
        tables_total_bytes += tab[1]
        tables_total_megabytes += tab[2]

    indices_total_bytes = 0
    indices_total_megabytes = 0.0
    for tab in indices:
        indices_total_bytes += tab[2]
        indices_total_megabytes += tab[3]

    print("SUMMARY")
    print(
        f"Total tables size: {pretty_int(tables_total_bytes)} B,"
        f" {pretty_float(tables_total_megabytes, 2)} MB"
    )
    print(
        f"Total indices size: {pretty_int(indices_total_bytes)} B,"
        f" {pretty_float(indices_total_megabytes, 2)} MB"
    )


def print_disclaimer():
    s = "NOTICE: gstat does not report size of blobs, so it is not included in above results"
    print(s)


def print_info():
    cmd = sys.argv[0]
    s = f"""
{cmd} version 1.0.0
This program parses output of Firebird's gstat utility and prints tables' and indices' sizes
in a nice tabular way.

Usage: 

    1. Generate data from gstat using command:
        gstat -a -u username -p password database_name > gstat_output_file.txt

    2. Run this program wiht the name of an output file as a parameter:
        python3 {cmd} gstat_output_file.txt

    3. You can also send output from gstat using shell pipe:
        cat gstat_output_file.txt | python {cmd}
        - or -
        gstat -a -u username -p password database_name | python3 {cmd}

    4. To print this message run command:
        python3 {cmd} --help
        python3 {cmd} -h
        python3 {cmd} -?
"""
    print(s)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h", "-?"]:
            print_info()
            exit()
    (tables, indices) = parse_gstat_output()
    print_tables_info(tables)
    print_indices_info(indices)
    print_summary(tables, indices)
    print_disclaimer()
