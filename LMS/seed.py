"""Seed the LMS with realistic demo data across 8 departments.

Usage:
    python seed.py            # seed only if database is empty
    python seed.py --reset    # wipe everything (DB + uploaded files) and reseed

8 departments x 8 semesters x 5 students = 320 students
8 departments x 8 semesters x 5 courses  = 320 courses
"""

import argparse
import os
import random
import uuid
from datetime import date, timedelta
from datetime import datetime, timezone

from app import create_app

app = create_app()

from app import db  # noqa: E402
from app.models import (  # noqa: E402
    Announcement,
    Assessment,
    Assignment,
    Attendance,
    Challan,
    Course,
    CourseResult,
    DEPARTMENTS,
    Enrollment,
    Mark,
    Student,
    Submission,
    Teacher,
    User,
    Warning,
    grade_for,
)
from app.models import utcnow  # noqa: E402

rng = random.Random(42)

TODAY = date.today()


def days_ago(n):
    return TODAY - timedelta(days=n)


def days_ahead(n):
    return TODAY + timedelta(days=n)


def hours_ago_dt(n):
    return utcnow() - timedelta(hours=n)


# --------------------------------------------------------------------------
# Department prefixes for course codes and roll numbers
# --------------------------------------------------------------------------
DEPT_PREFIX = {
    "BS AI": "AI",
    "BS CS": "CS",
    "BSE": "SE",
    "BDS": "DS",
    "BCYS": "CY",
    "BE AV": "AV",
    "BE EL": "EL",
    "BE MECH": "ME",
}

DEPT_ROLL_PREFIX = {
    "BS AI": "FA24-BAI",
    "BS CS": "FA24-BCS",
    "BSE": "FA24-BSE",
    "BDS": "FA24-BDS",
    "BCYS": "FA24-BCY",
    "BE AV": "FA24-BAV",
    "BE EL": "FA24-BEL",
    "BE MECH": "FA24-BME",
}

# --------------------------------------------------------------------------
# Courses per department per semester: (code, title, teacher, credit_hours)
# --------------------------------------------------------------------------
DEPT_COURSES = {
    "BS AI": {
        1: [
            ("AI-101", "Programming Fundamentals", "Dr. Sana Iqbal", 3),
            ("AI-102", "Calculus and Analytical Geometry", "Dr. Farah Deeba", 3),
            ("AI-103", "English Composition and Communication", "Ms. Ayesha Noor", 3),
            ("AI-104", "Introduction to Artificial Intelligence", "Prof. Tariq Mahmood", 3),
            ("AI-105", "Digital Logic Design", "Dr. Naveed Anwar", 3),
        ],
        2: [
            ("AI-201", "Object Oriented Programming", "Dr. Sana Iqbal", 3),
            ("AI-202", "Linear Algebra", "Dr. Asad Ullah", 3),
            ("AI-203", "Probability and Statistics", "Dr. Asad Ullah", 3),
            ("AI-204", "Data Structures and Algorithms", "Prof. Waqas Ahmed", 4),
            ("AI-205", "Discrete Structures", "Dr. Kamran Rasheed", 3),
        ],
        3: [
            ("AI-301", "Database Systems", "Dr. Hina Tariq", 3),
            ("AI-302", "Computer Networks", "Dr. Owais Malik", 3),
            ("AI-303", "Technical and Business Writing", "Ms. Ayesha Noor", 3),
            ("AI-304", "Machine Learning Fundamentals", "Prof. Adnan Rashid", 4),
            ("AI-305", "Software Engineering", "Dr. Hina Tariq", 3),
        ],
        4: [
            ("AI-401", "Deep Learning Fundamentals", "Prof. Adnan Rashid", 4),
            ("AI-402", "Operating Systems", "Prof. Kamran Rasheed", 4),
            ("AI-403", "Design and Analysis of Algorithms", "Dr. Kamran Rasheed", 3),
            ("AI-404", "Natural Language Processing", "Dr. Sana Iqbal", 3),
            ("AI-405", "Professional Practices", "Dr. Farah Deeba", 2),
        ],
        5: [
            ("AI-501", "Computer Vision", "Prof. Adnan Rashid", 4),
            ("AI-502", "Reinforcement Learning", "Dr. Sana Iqbal", 3),
            ("AI-503", "Knowledge Representation and Reasoning", "Prof. Tariq Mahmood", 3),
            ("AI-504", "Information Retrieval", "Dr. Owais Malik", 3),
            ("AI-505", "Pattern Recognition", "Dr. Hina Tariq", 3),
        ],
        6: [
            ("AI-601", "Expert Systems", "Prof. Tariq Mahmood", 3),
            ("AI-602", "Robotics and Intelligent Systems", "Dr. Naveed Anwar", 4),
            ("AI-603", "Data Mining", "Dr. Owais Malik", 3),
            ("AI-604", "Artificial Neural Networks", "Prof. Adnan Rashid", 3),
            ("AI-605", "AI Ethics and Society", "Ms. Ayesha Noor", 2),
        ],
        7: [
            ("AI-701", "Advanced Machine Learning", "Prof. Adnan Rashid", 4),
            ("AI-702", "Speech and Audio Processing", "Dr. Sana Iqbal", 3),
            ("AI-703", "Autonomous Systems", "Dr. Naveed Anwar", 3),
            ("AI-704", "AI Project I", "Prof. Tariq Mahmood", 3),
            ("AI-705", "Cloud Computing for AI", "Dr. Owais Malik", 3),
        ],
        8: [
            ("AI-801", "AI Project II", "Prof. Tariq Mahmood", 3),
            ("AI-802", "Big Data Analytics", "Dr. Hina Tariq", 3),
            ("AI-803", "Multi-Agent Systems", "Prof. Adnan Rashid", 3),
            ("AI-804", "Human-Computer Interaction", "Dr. Kamran Rasheed", 3),
            ("AI-805", "Generative AI and LLMs", "Dr. Sana Iqbal", 3),
        ],
    },
    "BS CS": {
        1: [
            ("CS-101", "Programming Fundamentals", "Prof. Adnan Sheikh", 3),
            ("CS-102", "Calculus and Analytical Geometry", "Dr. Farah Deeba", 3),
            ("CS-103", "English Composition and Communication", "Ms. Sana Mirza", 3),
            ("CS-104", "Introduction to ICT", "Dr. Owais Malik", 3),
            ("CS-105", "Digital Logic Design", "Dr. Naveed Anwar", 3),
        ],
        2: [
            ("CS-201", "Object Oriented Programming", "Prof. Adnan Sheikh", 3),
            ("CS-202", "Data Structures and Algorithms", "Prof. Waqas Ahmed", 4),
            ("CS-203", "Linear Algebra", "Dr. Asad Ullah", 3),
            ("CS-204", "Probability and Statistics", "Dr. Asad Ullah", 3),
            ("CS-205", "Discrete Structures", "Dr. Kamran Rasheed", 3),
        ],
        3: [
            ("CS-301", "Database Systems", "Dr. Hina Tariq", 3),
            ("CS-302", "Computer Networks", "Dr. Owais Malik", 3),
            ("CS-303", "Technical and Business Writing", "Ms. Sana Mirza", 3),
            ("CS-304", "Web Development", "Dr. Owais Malik", 3),
            ("CS-305", "Software Engineering", "Dr. Hina Tariq", 3),
        ],
        4: [
            ("CS-401", "Operating Systems", "Prof. Kamran Rasheed", 4),
            ("CS-402", "Theory of Automata", "Dr. Kamran Rasheed", 3),
            ("CS-403", "Design and Analysis of Algorithms", "Prof. Waqas Ahmed", 3),
            ("CS-404", "Web Engineering", "Dr. Owais Malik", 3),
            ("CS-405", "Professional Practices", "Dr. Farah Deeba", 2),
        ],
        5: [
            ("CS-501", "Compiler Construction", "Prof. Waqas Ahmed", 4),
            ("CS-502", "Computer Architecture", "Dr. Naveed Anwar", 3),
            ("CS-503", "Computer Graphics", "Prof. Adnan Sheikh", 3),
            ("CS-504", "Multimedia Systems", "Dr. Sana Iqbal", 3),
            ("CS-505", "Mobile Computing", "Dr. Owais Malik", 3),
        ],
        6: [
            ("CS-601", "Distributed Systems", "Dr. Owais Malik", 3),
            ("CS-602", "Information Security", "Dr. Naveed Anwar", 3),
            ("CS-603", "Parallel Computing", "Prof. Kamran Rasheed", 3),
            ("CS-604", "Introduction to Data Science", "Dr. Hina Tariq", 3),
            ("CS-605", "Elective I - Cloud Computing", "Dr. Owais Malik", 3),
        ],
        7: [
            ("CS-701", "Internet of Things", "Dr. Naveed Anwar", 3),
            ("CS-702", "Human Computer Interaction", "Dr. Sana Iqbal", 3),
            ("CS-703", "CS Project I", "Prof. Adnan Sheikh", 3),
            ("CS-704", "Elective II - Blockchain", "Prof. Waqas Ahmed", 3),
            ("CS-705", "Elective III - Bioinformatics", "Dr. Hina Tariq", 3),
        ],
        8: [
            ("CS-801", "CS Project II", "Prof. Adnan Sheikh", 3),
            ("CS-802", "Software Quality Engineering", "Dr. Hina Tariq", 3),
            ("CS-803", "Advanced Database Systems", "Dr. Owais Malik", 3),
            ("CS-804", "Network Security", "Dr. Naveed Anwar", 3),
            ("CS-805", "Research Methods in CS", "Prof. Kamran Rasheed", 3),
        ],
    },
    "BSE": {
        1: [
            ("SE-101", "Programming Fundamentals", "Dr. Rabia Aslam", 3),
            ("SE-102", "Calculus and Analytical Geometry", "Dr. Farah Deeba", 3),
            ("SE-103", "English Composition and Communication", "Ms. Sana Mirza", 3),
            ("SE-104", "Introduction to Software Engineering", "Prof. Zubair Hassan", 3),
            ("SE-105", "Digital Logic Design", "Dr. Naveed Anwar", 3),
        ],
        2: [
            ("SE-201", "Object Oriented Programming", "Dr. Rabia Aslam", 3),
            ("SE-202", "Data Structures and Algorithms", "Prof. Waqas Ahmed", 4),
            ("SE-203", "Linear Algebra", "Dr. Asad Ullah", 3),
            ("SE-204", "Discrete Structures", "Dr. Kamran Rasheed", 3),
            ("SE-205", "Probability and Statistics", "Dr. Asad Ullah", 3),
        ],
        3: [
            ("SE-301", "Requirements Engineering", "Prof. Zubair Hassan", 3),
            ("SE-302", "Database Systems", "Dr. Hina Tariq", 3),
            ("SE-303", "Web Development", "Dr. Owais Malik", 3),
            ("SE-304", "Technical and Business Writing", "Ms. Sana Mirza", 3),
            ("SE-305", "Computer Networks", "Dr. Owais Malik", 3),
        ],
        4: [
            ("SE-401", "Software Design and Architecture", "Prof. Zubair Hassan", 4),
            ("SE-402", "Operating Systems", "Prof. Kamran Rasheed", 4),
            ("SE-403", "Design and Analysis of Algorithms", "Dr. Kamran Rasheed", 3),
            ("SE-404", "Software Testing and Quality", "Dr. Rabia Aslam", 3),
            ("SE-405", "Human Computer Interaction", "Dr. Sana Iqbal", 3),
        ],
        5: [
            ("SE-501", "Software Project Management", "Prof. Zubair Hassan", 3),
            ("SE-502", "Mobile Application Development", "Dr. Owais Malik", 3),
            ("SE-503", "Information Security", "Dr. Naveed Anwar", 3),
            ("SE-504", "UX Design Principles", "Dr. Rabia Aslam", 3),
            ("SE-505", "Software Construction", "Prof. Adnan Sheikh", 3),
        ],
        6: [
            ("SE-601", "DevOps and Continuous Delivery", "Dr. Rabia Aslam", 3),
            ("SE-602", "Cloud Computing", "Dr. Owais Malik", 3),
            ("SE-603", "Data Mining", "Dr. Hina Tariq", 3),
            ("SE-604", "Agile Software Development", "Prof. Zubair Hassan", 3),
            ("SE-605", "Formal Methods", "Dr. Kamran Rasheed", 3),
        ],
        7: [
            ("SE-701", "Software Engineering Project I", "Prof. Zubair Hassan", 3),
            ("SE-702", "Enterprise Systems", "Dr. Owais Malik", 3),
            ("SE-703", "Service Oriented Architecture", "Dr. Hina Tariq", 3),
            ("SE-704", "Embedded Systems", "Dr. Naveed Anwar", 3),
            ("SE-705", "Software Elective - Microservices", "Dr. Rabia Aslam", 3),
        ],
        8: [
            ("SE-801", "Software Engineering Project II", "Prof. Zubair Hassan", 3),
            ("SE-802", "IT Project Management", "Dr. Rabia Aslam", 3),
            ("SE-803", "Software Metrics and Analysis", "Prof. Zubair Hassan", 3),
            ("SE-804", "Research Methods in SE", "Dr. Kamran Rasheed", 3),
            ("SE-805", "Software Elective II - AI for SE", "Dr. Sana Iqbal", 3),
        ],
    },
    "BDS": {
        1: [
            ("DS-101", "Programming Fundamentals", "Dr. Fatima Zahra", 3),
            ("DS-102", "Calculus and Analytical Geometry", "Dr. Farah Deeba", 3),
            ("DS-103", "English Composition and Communication", "Ms. Ayesha Noor", 3),
            ("DS-104", "Introduction to Data Science", "Dr. Hamza Pasha", 3),
            ("DS-105", "Statistics for Data Science", "Dr. Asad Ullah", 3),
        ],
        2: [
            ("DS-201", "Object Oriented Programming", "Dr. Fatima Zahra", 3),
            ("DS-202", "Data Structures and Algorithms", "Prof. Waqas Ahmed", 4),
            ("DS-203", "Linear Algebra for Data Science", "Dr. Asad Ullah", 3),
            ("DS-204", "Probability Theory", "Dr. Asad Ullah", 3),
            ("DS-205", "Discrete Mathematics", "Dr. Kamran Rasheed", 3),
        ],
        3: [
            ("DS-301", "Database Systems for Analytics", "Dr. Hina Tariq", 3),
            ("DS-302", "Data Wrangling and Preprocessing", "Dr. Fatima Zahra", 3),
            ("DS-303", "Statistical Methods", "Dr. Hamza Pasha", 3),
            ("DS-304", "Data Visualization", "Dr. Sana Iqbal", 3),
            ("DS-305", "Computer Networks", "Dr. Owais Malik", 3),
        ],
        4: [
            ("DS-401", "Machine Learning for Data Science", "Prof. Adnan Rashid", 4),
            ("DS-402", "Operating Systems", "Prof. Kamran Rasheed", 3),
            ("DS-403", "Design and Analysis of Algorithms", "Dr. Kamran Rasheed", 3),
            ("DS-404", "Big Data Fundamentals", "Dr. Hamza Pasha", 3),
            ("DS-405", "Research Methods", "Dr. Fatima Zahra", 3),
        ],
        5: [
            ("DS-501", "Deep Learning", "Prof. Adnan Rashid", 4),
            ("DS-502", "Time Series Analysis", "Dr. Hamza Pasha", 3),
            ("DS-503", "Data Engineering", "Dr. Owais Malik", 3),
            ("DS-504", "Natural Language Processing", "Dr. Sana Iqbal", 3),
            ("DS-505", "Information Retrieval", "Dr. Owais Malik", 3),
        ],
        6: [
            ("DS-601", "Bayesian Statistics", "Dr. Asad Ullah", 3),
            ("DS-602", "Data Mining Techniques", "Dr. Hina Tariq", 3),
            ("DS-603", "Cloud Computing for Analytics", "Dr. Owais Malik", 3),
            ("DS-604", "Design of Experiments", "Dr. Hamza Pasha", 3),
            ("DS-605", "Business Analytics", "Dr. Fatima Zahra", 3),
        ],
        7: [
            ("DS-701", "Advanced Predictive Analytics", "Prof. Adnan Rashid", 4),
            ("DS-702", "Data Science Project I", "Dr. Fatima Zahra", 3),
            ("DS-703", "High Performance Computing", "Dr. Naveed Anwar", 3),
            ("DS-704", "Text Analytics", "Dr. Sana Iqbal", 3),
            ("DS-705", "Elective - Geospatial Analytics", "Dr. Hamza Pasha", 3),
        ],
        8: [
            ("DS-801", "Data Science Project II", "Dr. Fatima Zahra", 3),
            ("DS-802", "AI Applications in Industry", "Prof. Adnan Rashid", 3),
            ("DS-803", "Data Governance and Ethics", "Dr. Hamza Pasha", 3),
            ("DS-804", "Prescriptive Analytics", "Dr. Asad Ullah", 3),
            ("DS-805", "Elective II - Healthcare Analytics", "Dr. Hina Tariq", 3),
        ],
    },
    "BCYS": {
        1: [
            ("CY-101", "Programming Fundamentals", "Dr. Imran Hayat", 3),
            ("CY-102", "Calculus and Analytical Geometry", "Dr. Farah Deeba", 3),
            ("CY-103", "English Composition and Communication", "Ms. Sana Mirza", 3),
            ("CY-104", "Introduction to Cyber Security", "Prof. Shahid Nawaz", 3),
            ("CY-105", "Digital Logic Design", "Dr. Naveed Anwar", 3),
        ],
        2: [
            ("CY-201", "Object Oriented Programming", "Dr. Imran Hayat", 3),
            ("CY-202", "Data Structures and Algorithms", "Prof. Waqas Ahmed", 4),
            ("CY-203", "Discrete Mathematics", "Dr. Kamran Rasheed", 3),
            ("CY-204", "Computer Networks", "Dr. Owais Malik", 3),
            ("CY-205", "Probability and Statistics", "Dr. Asad Ullah", 3),
        ],
        3: [
            ("CY-301", "Database Systems", "Dr. Hina Tariq", 3),
            ("CY-302", "Network Security Fundamentals", "Prof. Shahid Nawaz", 3),
            ("CY-303", "Operating Systems", "Prof. Kamran Rasheed", 4),
            ("CY-304", "Introduction to Cryptography", "Dr. Imran Hayat", 3),
            ("CY-305", "Technical Writing", "Ms. Sana Mirza", 3),
        ],
        4: [
            ("CY-401", "Web Security", "Dr. Owais Malik", 3),
            ("CY-402", "Ethical Hacking and Penetration Testing", "Prof. Shahid Nawaz", 4),
            ("CY-403", "Design and Analysis of Algorithms", "Dr. Kamran Rasheed", 3),
            ("CY-404", "Digital Forensics", "Dr. Imran Hayat", 3),
            ("CY-405", "Information Assurance", "Dr. Naveed Anwar", 3),
        ],
        5: [
            ("CY-501", "Malware Analysis", "Dr. Imran Hayat", 3),
            ("CY-502", "Advanced Penetration Testing", "Prof. Shahid Nawaz", 4),
            ("CY-503", "Wireless and Mobile Security", "Dr. Naveed Anwar", 3),
            ("CY-504", "Cloud Security", "Dr. Owais Malik", 3),
            ("CY-505", "Security Architecture", "Prof. Shahid Nawaz", 3),
        ],
        6: [
            ("CY-601", "Incident Response and Management", "Prof. Shahid Nawaz", 3),
            ("CY-602", "Security Audit and Compliance", "Dr. Imran Hayat", 3),
            ("CY-603", "Mobile Application Security", "Dr. Owais Malik", 3),
            ("CY-604", "Risk Management", "Dr. Hina Tariq", 3),
            ("CY-605", "IoT Security", "Dr. Naveed Anwar", 3),
        ],
        7: [
            ("CY-701", "Cyber Law and Forensics", "Prof. Shahid Nawaz", 3),
            ("CY-702", "Cyber Security Project I", "Dr. Imran Hayat", 3),
            ("CY-703", "Advanced Cryptography", "Dr. Kamran Rasheed", 3),
            ("CY-704", "Threat Intelligence and Hunting", "Prof. Shahid Nawaz", 3),
            ("CY-705", "Elective - Blockchain Security", "Dr. Owais Malik", 3),
        ],
        8: [
            ("CY-801", "Cyber Security Project II", "Dr. Imran Hayat", 3),
            ("CY-802", "Cyber Warfare and Defense", "Prof. Shahid Nawaz", 3),
            ("CY-803", "Security Operations Center", "Prof. Shahid Nawaz", 3),
            ("CY-804", "Privacy and Data Protection", "Dr. Hina Tariq", 3),
            ("CY-805", "Elective II - Reverse Engineering", "Dr. Naveed Anwar", 3),
        ],
    },
    "BE AV": {
        1: [
            ("AV-101", "Programming Fundamentals", "Dr. Aliya Bashir", 3),
            ("AV-102", "Calculus and Analytical Geometry", "Dr. Farah Deeba", 3),
            ("AV-103", "English Composition and Communication", "Ms. Ayesha Noor", 3),
            ("AV-104", "Introduction to Media Technology", "Prof. Danish Khan", 3),
            ("AV-105", "Digital Logic Design", "Dr. Naveed Anwar", 3),
        ],
        2: [
            ("AV-201", "Object Oriented Programming", "Dr. Aliya Bashir", 3),
            ("AV-202", "Data Structures", "Prof. Waqas Ahmed", 3),
            ("AV-203", "Linear Algebra", "Dr. Asad Ullah", 3),
            ("AV-204", "Applied Physics", "Dr. Naveed Anwar", 3),
            ("AV-205", "Visual Communication Design", "Prof. Danish Khan", 3),
        ],
        3: [
            ("AV-301", "Digital Audio Production", "Prof. Danish Khan", 3),
            ("AV-302", "Video Production and Editing", "Dr. Aliya Bashir", 3),
            ("AV-303", "Database Systems", "Dr. Hina Tariq", 3),
            ("AV-304", "Signal Processing", "Dr. Naveed Anwar", 3),
            ("AV-305", "Computer Networks", "Dr. Owais Malik", 3),
        ],
        4: [
            ("AV-401", "Sound Engineering", "Prof. Danish Khan", 4),
            ("AV-402", "Animation Fundamentals", "Dr. Aliya Bashir", 3),
            ("AV-403", "Operating Systems", "Prof. Kamran Rasheed", 3),
            ("AV-404", "Algorithms", "Dr. Kamran Rasheed", 3),
            ("AV-405", "Color Science and Grading", "Prof. Danish Khan", 3),
        ],
        5: [
            ("AV-501", "3D Modeling and Rendering", "Dr. Aliya Bashir", 4),
            ("AV-502", "VFX Compositing", "Prof. Danish Khan", 3),
            ("AV-503", "Motion Graphics", "Dr. Aliya Bashir", 3),
            ("AV-504", "Broadcasting Technology", "Dr. Naveed Anwar", 3),
            ("AV-505", "Human Computer Interaction", "Dr. Sana Iqbal", 3),
        ],
        6: [
            ("AV-601", "Game Audio Design", "Prof. Danish Khan", 3),
            ("AV-602", "Post Production Techniques", "Dr. Aliya Bashir", 3),
            ("AV-603", "AR and VR Fundamentals", "Dr. Owais Malik", 3),
            ("AV-604", "Media Law and Ethics", "Ms. Ayesha Noor", 2),
            ("AV-605", "Streaming Technology", "Dr. Naveed Anwar", 3),
        ],
        7: [
            ("AV-701", "AV Engineering Project I", "Prof. Danish Khan", 3),
            ("AV-702", "Immersive Media Design", "Dr. Aliya Bashir", 3),
            ("AV-703", "Film Production Technology", "Prof. Danish Khan", 3),
            ("AV-704", "Acoustics and Room Design", "Dr. Naveed Anwar", 3),
            ("AV-705", "Elective - Interactive Media", "Dr. Aliya Bashir", 3),
        ],
        8: [
            ("AV-801", "AV Engineering Project II", "Prof. Danish Khan", 3),
            ("AV-802", "Media Asset Management", "Dr. Aliya Bashir", 3),
            ("AV-803", "Content Distribution Systems", "Dr. Owais Malik", 3),
            ("AV-804", "AV Systems Design", "Dr. Naveed Anwar", 3),
            ("AV-805", "Elective II - AI in Media", "Dr. Sana Iqbal", 3),
        ],
    },
    "BE EL": {
        1: [
            ("EL-101", "Programming Fundamentals", "Dr. Kashif Raza", 3),
            ("EL-102", "Calculus and Analytical Geometry", "Dr. Farah Deeba", 3),
            ("EL-103", "English Composition and Communication", "Ms. Sana Mirza", 3),
            ("EL-104", "Introduction to Electrical Engineering", "Prof. Asif Mehmood", 3),
            ("EL-105", "Applied Physics", "Dr. Naveed Anwar", 3),
        ],
        2: [
            ("EL-201", "Circuit Analysis", "Prof. Asif Mehmood", 3),
            ("EL-202", "Object Oriented Programming", "Dr. Kashif Raza", 3),
            ("EL-203", "Data Structures", "Prof. Waqas Ahmed", 3),
            ("EL-204", "Linear Algebra", "Dr. Asad Ullah", 3),
            ("EL-205", "Differential Equations", "Dr. Asad Ullah", 3),
        ],
        3: [
            ("EL-301", "Electronics I", "Prof. Asif Mehmood", 4),
            ("EL-302", "Digital Logic Design", "Dr. Naveed Anwar", 3),
            ("EL-303", "Signals and Systems", "Dr. Kashif Raza", 3),
            ("EL-304", "Electromagnetics", "Prof. Asif Mehmood", 3),
            ("EL-305", "Probability and Random Processes", "Dr. Asad Ullah", 3),
        ],
        4: [
            ("EL-401", "Electronics II", "Prof. Asif Mehmood", 4),
            ("EL-402", "Control Systems", "Dr. Kashif Raza", 3),
            ("EL-403", "Power Systems", "Prof. Asif Mehmood", 3),
            ("EL-404", "Computer Architecture", "Dr. Naveed Anwar", 3),
            ("EL-405", "Numerical Methods", "Dr. Asad Ullah", 3),
        ],
        5: [
            ("EL-501", "Power Electronics", "Prof. Asif Mehmood", 4),
            ("EL-502", "Communication Systems", "Dr. Kashif Raza", 3),
            ("EL-503", "Instrumentation and Measurement", "Dr. Naveed Anwar", 3),
            ("EL-504", "Microprocessors and Microcontrollers", "Dr. Kashif Raza", 3),
            ("EL-505", "Filter Design", "Prof. Asif Mehmood", 3),
        ],
        6: [
            ("EL-601", "Electrical Machines", "Prof. Asif Mehmood", 4),
            ("EL-602", "PLC and SCADA Systems", "Dr. Kashif Raza", 3),
            ("EL-603", "Renewable Energy Systems", "Prof. Asif Mehmood", 3),
            ("EL-604", "Embedded Systems Design", "Dr. Naveed Anwar", 3),
            ("EL-605", "Power System Protection", "Dr. Kashif Raza", 3),
        ],
        7: [
            ("EL-701", "Power System Analysis", "Prof. Asif Mehmood", 4),
            ("EL-702", "EE Project I", "Dr. Kashif Raza", 3),
            ("EL-703", "High Voltage Engineering", "Prof. Asif Mehmood", 3),
            ("EL-704", "Industrial Automation", "Dr. Naveed Anwar", 3),
            ("EL-705", "Elective - Power Electronics Drives", "Dr. Kashif Raza", 3),
        ],
        8: [
            ("EL-801", "EE Project II", "Dr. Kashif Raza", 3),
            ("EL-802", "Smart Grid Technology", "Prof. Asif Mehmood", 3),
            ("EL-803", "Electric Drives and Traction", "Prof. Asif Mehmood", 3),
            ("EL-804", "Power Quality", "Dr. Kashif Raza", 3),
            ("EL-805", "Elective II - Solar Energy Systems", "Prof. Asif Mehmood", 3),
        ],
    },
    "BE MECH": {
        1: [
            ("ME-101", "Programming Fundamentals", "Dr. Tahir Hussain", 3),
            ("ME-102", "Calculus and Analytical Geometry", "Dr. Farah Deeba", 3),
            ("ME-103", "English Composition and Communication", "Ms. Ayesha Noor", 3),
            ("ME-104", "Introduction to Mechanical Engineering", "Prof. Tanveer Alam", 3),
            ("ME-105", "Applied Physics", "Dr. Naveed Anwar", 3),
        ],
        2: [
            ("ME-201", "Engineering Statics", "Prof. Tanveer Alam", 3),
            ("ME-202", "Engineering Dynamics", "Prof. Tanveer Alam", 3),
            ("ME-203", "Object Oriented Programming", "Dr. Tahir Hussain", 3),
            ("ME-204", "Data Structures", "Prof. Waqas Ahmed", 3),
            ("ME-205", "Linear Algebra", "Dr. Asad Ullah", 3),
        ],
        3: [
            ("ME-301", "Thermodynamics", "Prof. Tanveer Alam", 4),
            ("ME-302", "Fluid Mechanics", "Dr. Tahir Hussain", 3),
            ("ME-303", "Material Science", "Prof. Tanveer Alam", 3),
            ("ME-304", "Manufacturing Processes", "Dr. Tahir Hussain", 3),
            ("ME-305", "Engineering Drawing and CAD", "Prof. Tanveer Alam", 3),
        ],
        4: [
            ("ME-401", "Heat Transfer", "Prof. Tanveer Alam", 4),
            ("ME-402", "Machine Design I", "Dr. Tahir Hussain", 3),
            ("ME-403", "Mechanics of Materials", "Prof. Tanveer Alam", 3),
            ("ME-404", "CAD/CAM", "Dr. Tahir Hussain", 3),
            ("ME-405", "Numerical Methods", "Dr. Asad Ullah", 3),
        ],
        5: [
            ("ME-501", "Internal Combustion Engines", "Prof. Tanveer Alam", 4),
            ("ME-502", "HVAC Systems", "Dr. Tahir Hussain", 3),
            ("ME-503", "Dynamics of Machines", "Prof. Tanveer Alam", 3),
            ("ME-504", "Industrial Engineering", "Dr. Tahir Hussain", 3),
            ("ME-505", "Control Systems", "Dr. Kashif Raza", 3),
        ],
        6: [
            ("ME-601", "Turbo Machines", "Prof. Tanveer Alam", 3),
            ("ME-602", "Advanced CAD and FEA", "Dr. Tahir Hussain", 3),
            ("ME-603", "Finite Element Analysis", "Dr. Tahir Hussain", 3),
            ("ME-604", "Robotics for Manufacturing", "Dr. Naveed Anwar", 3),
            ("ME-605", "Mechatronics", "Dr. Kashif Raza", 3),
        ],
        7: [
            ("ME-701", "ME Project I", "Prof. Tanveer Alam", 3),
            ("ME-702", "Automobile Engineering", "Prof. Tanveer Alam", 3),
            ("ME-703", "Power Plant Engineering", "Dr. Tahir Hussain", 3),
            ("ME-704", "CNC Technology", "Dr. Tahir Hussain", 3),
            ("ME-705", "Elective - Aerospace Engineering", "Prof. Tanveer Alam", 3),
        ],
        8: [
            ("ME-801", "ME Project II", "Prof. Tanveer Alam", 3),
            ("ME-802", "Total Quality Management", "Dr. Tahir Hussain", 3),
            ("ME-803", "Supply Chain Management", "Dr. Tahir Hussain", 3),
            ("ME-804", "Energy Systems", "Prof. Tanveer Alam", 3),
            ("ME-805", "Elective II - Biomechanics", "Dr. Tahir Hussain", 3),
        ],
    },
}

# --------------------------------------------------------------------------
# Name pools for generating students
# --------------------------------------------------------------------------
FIRST_NAMES_MALE = [
    "Ahmed", "Ali", "Bilal", "Hamza", "Hassan", "Hussain", "Imran", "Kamran",
    "Kashif", "Muhammad", "Omar", "Saad", "Tariq", "Usman", "Waqar", "Zain",
    "Fahad", "Faisal", "Farhan", "Haris", "Irfan", "Junaid", "Khalid", "Nasir",
    "Rizwan", "Salman", "Shahid", "Taimur", "Yasir", "Zubair", "Adeel", "Babar",
    "Danish", "Ehsan", "Farrukh", "Ghulam", "Hammad", "Iftikhar", "Javed", "Kamran",
    "Luqman", "Mudassar", "Nabeel", "Rashid", "Sohail", "Taha", "Waleed", "Zahid",
]

FIRST_NAMES_FEMALE = [
    "Aisha", "Amna", "Areeba", "Asma", "Fatima", "Hira", "Iqra", "Kiran",
    "Laiba", "Maham", "Mariam", "Mehwish", "Nadia", "Nida", "Nimra", "Rabia",
    "Sadia", "Sana", "Sara", "Sumaira", "Tania", "Uzma", "Zainab", "Zara",
    "Anum", "Bushra", "Dua", "Elina", "Fariha", "Ghazal", "Hina", "Iram",
    "Javeria", "Kinza", "Lubna", "Madiha", "Nida", "Quratulain", "Rida", "Sehar",
    "Shifa", "Tayyaba", "Urooj", "Warda", "Yasmin", "Zehra", "Aimen", "Batool",
]

LAST_NAMES = [
    "Khan", "Ahmed", "Ali", "Hussain", "Shah", "Malik", "Butt", "Chaudhry",
    "Iqbal", "Raza", "Sheikh", "Qureshi", "Siddiqui", "Mirza", "Baig",
    "Tariq", "Aslam", "Rashid", "Anwar", "Hassan", "Raza", "Javed", "Akram",
    "Rehman", "Saeed", "Farooq", "Nawaz", "Sohail", "Yousaf", "Kamal",
]

# --------------------------------------------------------------------------
# Fee / assessment / assignment reference data
# --------------------------------------------------------------------------
FEE_AMOUNTS = {
    "Tuition Fee": (45000, 52000),
    "Exam Fee": (3000, 5000),
    "Hostel Fee": (30000, 38000),
    "Library Fine": (200, 800),
    "Late Fee": (500, 1500),
    "Admission Fee": (25000, 25000),
}
FEE_TYPES = list(FEE_AMOUNTS)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def weekday_dates(count):
    dates = []
    d = TODAY
    while len(dates) < count:
        if d.weekday() < 5:
            dates.append(d)
        d -= timedelta(days=1)
    return list(reversed(dates))


def add_attendance(enrollment, present, late, absent, excused):
    statuses = ["present"] * present + ["late"] * late + ["absent"] * absent + ["excused"] * excused
    rng.shuffle(statuses)
    for d, s in zip(weekday_dates(len(statuses)), statuses):
        db.session.add(Attendance(enrollment_id=enrollment.id, date=d, status=s))


def generic_attendance(enrollment, rate=None):
    n = rng.randint(20, 27)
    late = rng.randint(0, 3)
    excused = rng.randint(0, 2)
    rate = rate if rate is not None else rng.uniform(0.86, 0.98)
    present = max(1, int((n - late - excused) * rate + 0.5))
    absent = n - late - excused - present
    add_attendance(enrollment, present, late, max(0, absent), excused)


def half_up(value):
    return int(value + 0.5)


def add_marks(enrollment, target_pct, jitter=0.0):
    for a in enrollment.course.assessments:
        t = target_pct + (rng.uniform(-jitter, jitter) if jitter else 0.0)
        t = max(0.0, min(100.0, t))
        obtained = max(0, min(a.total_marks, half_up(a.total_marks * t / 100.0)))
        db.session.add(
            Mark(assessment_id=a.id, student_id=enrollment.student_id, obtained_marks=float(obtained))
        )


def finalize(enrollment, target_pct, jitter=0.0, days_ago_finalized=20):
    add_marks(enrollment, target_pct, jitter)
    db.session.flush()
    pct = CourseResult.compute_percentage(enrollment)
    letter, points = grade_for(pct)
    db.session.add(
        CourseResult(
            enrollment_id=enrollment.id,
            percentage=pct,
            grade_letter=letter,
            grade_points=points,
            is_finalized=True,
            finalized_on=utcnow() - timedelta(days=days_ago_finalized),
        )
    )


_challan_seq = {}
_receipt_seq = {}


def next_challan_no(issue_date):
    key = issue_date.strftime("%Y%m")
    _challan_seq[key] = _challan_seq.get(key, 0) + 1
    return f"CH-{key}-{_challan_seq[key]:04d}"


def next_receipt_no(paid_date):
    key = paid_date.strftime("%Y%m")
    _receipt_seq[key] = _receipt_seq.get(key, 0) + 1
    return f"RC-{key}-{_receipt_seq[key]:04d}"


def add_challan(student, fee_type, issue, due, status, paid_on=None):
    lo, hi = FEE_AMOUNTS[fee_type]
    amount = rng.randint(lo, hi)
    challan = Challan(
        student_id=student.id,
        challan_no=next_challan_no(issue),
        fee_type=fee_type,
        description=f"{fee_type} — Fall {TODAY.year}",
        amount=amount,
        issue_date=issue,
        due_date=due,
        status=status,
        paid_date=paid_on,
        receipt_no=next_receipt_no(paid_on) if paid_on else None,
    )
    db.session.add(challan)
    db.session.flush()
    return challan


def add_warning(student, wtype, severity, title, message, source="manual",
                created=None, is_read=False, related_challan=None):
    created = created or (utcnow() - timedelta(days=rng.randint(1, 25)))
    warning = Warning(
        student_id=student.id,
        type=wtype,
        severity=severity,
        title=title,
        message=message,
        source=source,
        related_challan_id=related_challan.id if related_challan else None,
        is_read=is_read,
        read_at=(created + timedelta(hours=rng.randint(2, 48))) if is_read else None,
        created_at=created,
    )
    db.session.add(warning)
    return warning


def add_submission(assignment, student, graded=None, days_before_due=2):
    submitted_at = assignment.due_date - timedelta(days=days_before_due)
    submission = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        stored_filename="pending",
        original_filename=f"{assignment.title.split(' — ')[0]}_{student.roll_no}.txt",
        submitted_at=submitted_at,
        created_at=submitted_at,
    )
    if graded is not None:
        submission.marks = float(max(0, min(assignment.total_marks, half_up(assignment.total_marks * graded))))
        submission.feedback = "Good effort. Watch the edge cases and add comments next time."
    db.session.add(submission)
    db.session.flush()

    submission.stored_filename = f"{submission.id}_{uuid.uuid4().hex}.txt"
    path = os.path.join(app.config["UPLOAD_FOLDER"], submission.stored_filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            f"Demo submission\n"
            f"Assignment : {assignment.title} ({assignment.course.code})\n"
            f"Student    : {student.user.full_name} ({student.roll_no})\n"
            f"Submitted  : {submitted_at:%d %b %Y}\n"
            f"\nThis is a seeded placeholder file for the LMS demo.\n"
        )
    return submission


# --------------------------------------------------------------------------
# Name generator
# --------------------------------------------------------------------------
def generate_names(count):
    used = set()
    names = []
    all_first = FIRST_NAMES_MALE + FIRST_NAMES_FEMALE
    while len(names) < count:
        first = rng.choice(all_first)
        last = rng.choice(LAST_NAMES)
        full = f"{first} {last}"
        if full not in used:
            used.add(full)
            names.append(full)
    return names


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def reset_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        upload_dir = app.config["UPLOAD_FOLDER"]
        removed = 0
        for name in os.listdir(upload_dir):
            if name == ".gitkeep":
                continue
            os.remove(os.path.join(upload_dir, name))
            removed += 1
        print(f"Reset: dropped all tables, removed {removed} uploaded file(s).")


def seed():
    # ---- admin -----------------------------------------------------------
    admin_user = User(
        email="admin@university.edu.pk",
        full_name="Dr. Imran Qureshi",
        role="admin",
    )
    admin_user.set_password("admin123")
    db.session.add(admin_user)
    db.session.flush()

    # ---- create teachers for all departments -----------------------------
    teachers = {}  # (dept, teacher_name) -> Teacher
    teacher_emails = set()
    emp_counter = 1
    for dept, semesters in DEPT_COURSES.items():
        unique_names = []
        seen = set()
        for sem, course_list in semesters.items():
            for code, title, teacher_name, ch in course_list:
                if teacher_name not in seen:
                    seen.add(teacher_name)
                    unique_names.append(teacher_name)
        for tname in unique_names:
            email_base = tname.lower().replace(" ", ".").replace(".", "")
            email = f"{email_base}@university.edu.pk"
            counter = 1
            while email in teacher_emails or User.query.filter_by(email=email).first():
                email = f"{email_base}{counter}@university.edu.pk"
                counter += 1
            teacher_emails.add(email)

            tuser = User(email=email, full_name=tname, role="teacher")
            tuser.set_password("teacher123")
            db.session.add(tuser)
            db.session.flush()

            emp_id = f"EMP-{DEPT_PREFIX[dept]}-{emp_counter:03d}"
            emp_counter += 1
            teacher_rec = Teacher(
                user_id=tuser.id,
                department=dept,
                semester=1,
                employee_id=emp_id,
                phone=f"03{rng.randint(10, 45)}-{rng.randint(2000000, 9999999)}",
            )
            db.session.add(teacher_rec)
            db.session.flush()
            teachers[(dept, tname)] = teacher_rec

    # ---- generate all student names (320 + 3 CampusGuard) ----------------
    all_names = generate_names(320)
    name_idx = 0

    # ---- create courses for all departments ------------------------------
    courses = {}  # code -> Course
    for dept, semesters in DEPT_COURSES.items():
        for sem, course_list in semesters.items():
            for code, title, teacher, ch in course_list:
                teacher_rec = teachers.get((dept, teacher))
                course = Course(
                    code=code, title=title, teacher=teacher,
                    teacher_id=teacher_rec.id if teacher_rec else None,
                    credit_hours=ch, semester=sem, department=dept,
                )
                db.session.add(course)
                courses[code] = course
    db.session.flush()

    # ---- create students for all departments -----------------------------
    all_students = []  # list of (student, dept, semester)
    used_emails = set()

    for dept in DEPARTMENTS:
        prefix = DEPT_ROLL_PREFIX[dept]
        roll_counter = 1
        for sem in range(1, 9):
            for _ in range(5):
                full_name = all_names[name_idx]
                name_idx += 1

                email_base = full_name.lower().replace(" ", ".")
                email = f"{email_base}@university.edu.pk"
                counter = 1
                while email in used_emails:
                    email = f"{email_base}{counter}@university.edu.pk"
                    counter += 1
                used_emails.add(email)

                user = User(email=email, full_name=full_name, role="student")
                user.set_password("student123")
                db.session.add(user)
                db.session.flush()

                roll_no = f"{prefix}-{roll_counter:03d}"
                roll_counter += 1

                student = Student(
                    user_id=user.id,
                    roll_no=roll_no,
                    program=dept,
                    semester=sem,
                    phone=f"03{rng.randint(10, 45)}-{rng.randint(2000000, 9999999)}",
                )
                db.session.add(student)
                all_students.append((student, dept, sem))

    db.session.flush()

    # ---- CampusGuard AI students -----------------------------------------
    for cg_name, cg_roll, cg_email in [
        ("Muhammad Yasir Soomro", "SE-001", "yasirsoomro468@gmail.com"),
        ("Amal Fatima", "SE-002", "amalfatima12020@gmail.com"),
        ("Sualeha Jameel", "SE-003", "sualehajameel72@gmail.com"),
    ]:
        cg_user = User(email=cg_email, full_name=cg_name, role="student")
        cg_user.set_password("student123")
        db.session.add(cg_user)
        db.session.flush()
        db.session.add(
            Student(user_id=cg_user.id, roll_no=cg_roll,
                    program="BSE", semester=3)
        )
    db.session.flush()

    # ---- assessments for every course ------------------------------------
    for code, course in courses.items():
        if course.credit_hours >= 4:
            plan = [
                ("Quiz 1", "quiz", 20, 10),
                ("Quiz 2", "quiz", 20, 10),
                ("Midterm", "midterm", 50, 30),
                ("Final Exam", "final", 100, 50),
            ]
        else:
            plan = [
                ("Quiz 1", "quiz", 20, 15),
                ("Midterm", "midterm", 50, 35),
                ("Final Exam", "final", 100, 50),
            ]
        for title, atype, total, weight in plan:
            db.session.add(
                Assessment(course_id=course.id, title=title, type=atype,
                           total_marks=total, weightage=weight)
            )
    db.session.flush()

    # ---- assignments for every course ------------------------------------
    all_assignments = {}
    for code, course in courses.items():
        prefix = code.rsplit("-", 1)[0]
        pair = []
        for idx in range(1, 3):
            if course.semester <= 4:
                due = datetime.combine(
                    days_ago(30 - idx * 10), datetime.min.time()
                ).replace(hour=23, minute=59)
            else:
                due = datetime.combine(
                    days_ago(8) if idx == 1 else days_ahead(9),
                    datetime.min.time()
                ).replace(hour=23, minute=59)
            assignment = Assignment(
                course_id=course.id,
                title=f"Assignment {idx} — {course.title[:30]}",
                description="Submit your solution as a PDF/ZIP through the portal before the deadline.",
                due_date=due.replace(tzinfo=timezone.utc),
                total_marks=50 if course.credit_hours <= 3 else 100,
                created_at=utcnow() - timedelta(days=45),
            )
            db.session.add(assignment)
            pair.append(assignment)
        all_assignments[code] = pair
    db.session.flush()

    # ---- enrollments: each student in ALL courses from sem 1 to current --
    enrollment_map = {}  # (student_id, code) -> Enrollment
    current_sem_codes = {}  # student_id -> set of codes for current semester
    for student, dept, sem in all_students:
        dept_courses = DEPT_COURSES[dept]
        cur_codes = set()
        for s in range(1, sem + 1):
            for code, title, teacher, ch in dept_courses[s]:
                e = Enrollment(
                    student_id=student.id,
                    course_id=courses[code].id,
                    enrolled_on=days_ago(110),
                )
                db.session.add(e)
                db.session.flush()
                enrollment_map[(student.id, code)] = e
                if s == sem:
                    cur_codes.add(code)
        current_sem_codes[student.id] = cur_codes

    # CampusGuard students enroll in BSE semesters 1-3 courses
    cg_students = Student.query.filter(Student.roll_no.in_(["SE-001", "SE-002", "SE-003"])).all()
    bse_all_depts = DEPT_COURSES["BSE"]
    cg_sem3_codes = set()
    for code, title, teacher, ch in bse_all_depts[3]:
        cg_sem3_codes.add(code)
    for cg_st in cg_students:
        for s in range(1, 4):
            for code, title, teacher, ch in bse_all_depts[s]:
                e = Enrollment(
                    student_id=cg_st.id,
                    course_id=courses[code].id,
                    enrolled_on=days_ago(110),
                )
                db.session.add(e)
                db.session.flush()
                enrollment_map[(cg_st.id, code)] = e

    # ---- attendance for current semester enrollments only ----------------
    cg_ids = {cg.id for cg in cg_students}
    for (sid, code), enr in enrollment_map.items():
        is_current = code in current_sem_codes.get(sid, set())
        is_cg_current = sid in cg_ids and code in cg_sem3_codes
        if is_current or is_cg_current:
            generic_attendance(enr)
    db.session.flush()

    # ---- marks + results -------------------------------------------------
    # For semesters < student's current semester: finalize results
    # For current semester: partial marks (quizzes only) -> "In Progress"
    for student, dept, sem in all_students:
        dept_courses = DEPT_COURSES[dept]
        for past_sem in range(1, sem):
            for code, title, teacher, ch in dept_courses[past_sem]:
                enr = enrollment_map.get((student.id, code))
                if enr:
                    target = rng.uniform(55, 95)
                    finalize(enr, target, jitter=8, days_ago_finalized=rng.randint(30, 200))

        # current semester: partial marks (quizzes only)
        for code, title, teacher, ch in dept_courses[sem]:
            enr = enrollment_map.get((student.id, code))
            if enr:
                target = rng.uniform(55, 92)
                for a in enr.course.assessments:
                    if a.type != "quiz":
                        continue
                    obtained = max(0, min(a.total_marks, half_up(a.total_marks * target / 100.0)))
                    db.session.add(
                        Mark(assessment_id=a.id, student_id=enr.student_id, obtained_marks=float(obtained))
                    )

    # CampusGuard students: finalize BSE sem 1 and 2, partial for sem 3
    bse_all = DEPT_COURSES["BSE"]
    for cg_st in cg_students:
        for past_sem in [1, 2]:
            for code, title, teacher, ch in bse_all[past_sem]:
                enr = enrollment_map.get((cg_st.id, code))
                if enr:
                    target = rng.uniform(60, 88)
                    finalize(enr, target, jitter=8, days_ago_finalized=rng.randint(30, 200))
        for code, title, teacher, ch in bse_all[3]:
            enr = enrollment_map.get((cg_st.id, code))
            if enr:
                target = rng.uniform(60, 85)
                for a in enr.course.assessments:
                    if a.type != "quiz":
                        continue
                    obtained = max(0, min(a.total_marks, half_up(a.total_marks * target / 100.0)))
                    db.session.add(
                        Mark(assessment_id=a.id, student_id=enr.student_id, obtained_marks=float(obtained))
                    )
    db.session.flush()

    # ---- submissions (sample for current semester courses) ---------------
    for student, dept, sem in all_students:
        for code, title, teacher, ch in DEPT_COURSES[dept][sem]:
            for assignment in all_assignments.get(code, []):
                if assignment.due_date <= utcnow():
                    if rng.random() < 0.6:
                        graded = rng.uniform(0.55, 0.95) if rng.random() < 0.5 else None
                        add_submission(assignment, student, graded=graded,
                                       days_before_due=rng.randint(1, 5))
    db.session.flush()

    # ---- challans (2-3 per student, mix of statuses) ---------------------
    for student, dept, sem in all_students:
        num_challans = rng.randint(2, 3)
        for i in range(num_challans):
            fee_type = rng.choice(FEE_TYPES)
            if rng.random() < 0.65:
                add_challan(student, fee_type, days_ago(rng.randint(30, 90)),
                            days_ago(rng.randint(1, 20)), "paid",
                            paid_on=days_ago(rng.randint(1, 15)))
            elif rng.random() < 0.5:
                add_challan(student, fee_type, days_ago(rng.randint(5, 20)),
                            days_ahead(rng.randint(1, 10)), "unpaid")
            else:
                add_challan(student, fee_type, days_ago(rng.randint(20, 40)),
                            days_ago(rng.randint(1, 10)), "unpaid")
    db.session.flush()

    # ---- warnings (random subset of students) ----------------------------
    warning_types = ["attendance", "fee", "disciplinary"]
    severities = ["info", "warning", "critical"]
    warning_count = 0
    for student, dept, sem in all_students:
        if rng.random() < 0.35:
            wtype = rng.choice(warning_types)
            severity = rng.choice(severities)
            if wtype == "attendance":
                title = f"Low Attendance Warning — {dept}"
                message = (
                    f"Dear {student.user.full_name},\n\n"
                    f"Your attendance has fallen below the required 75% threshold. "
                    f"Please improve your attendance immediately to avoid debarment from exams."
                )
            elif wtype == "fee":
                title = "Fee Payment Reminder"
                message = (
                    f"Dear {student.user.full_name},\n\n"
                    f"Your fee challan is overdue. Please clear your dues at the earliest "
                    f"to avoid late fee penalties and registration holds."
                )
            else:
                title = "Disciplinary Notice"
                message = (
                    f"Dear {student.user.full_name},\n\n"
                    f"This is to inform you of a disciplinary concern. Please visit the "
                    f"department office for further details."
                )
            add_warning(
                student, wtype, severity, title, message,
                source=rng.choice(["manual", "system", "api"]),
                is_read=rng.random() < 0.4,
            )
            warning_count += 1
    db.session.flush()

    # ---- announcements ---------------------------------------------------
    db.session.add_all([
        Announcement(
            title="Fall 2026 Midterm Examination Schedule",
            body="Midterm examinations begin next Monday. The detailed date sheet is now available "
                 "on the notice board and outside the exam cell. Students must carry their university "
                 "ID cards to every paper.",
            is_pinned=True,
            created_at=utcnow() - timedelta(days=4),
        ),
        Announcement(
            title="Fee Submission Deadline — Fall 2026",
            body="All tuition fee challans must be cleared before the deadline. After the due date, "
                 "a late fee penalty applies and semester registration may be put on hold.",
            is_pinned=True,
            expires_on=days_ahead(10),
            created_at=utcnow() - timedelta(days=6),
        ),
        Announcement(
            title="Library Timings during Midterms",
            body="The central library will remain open from 8 AM to 10 PM throughout the midterm week.",
            expires_on=days_ago(3),
            created_at=utcnow() - timedelta(days=20),
        ),
        Announcement(
            title="LMS Portal Maintenance — Saturday 10 PM",
            body="The LMS portal will be briefly unavailable on Saturday between 10 PM and 11 PM "
                 "for scheduled maintenance. Plan your assignment submissions accordingly.",
            created_at=utcnow() - timedelta(days=2),
        ),
        Announcement(
            title="Need-Based Scholarship Applications Open",
            body="Applications for the need-based scholarship for Fall 2026 are now open. Collect "
                 "the form from the financial aid office and submit before the end of the month.",
            expires_on=days_ahead(21),
            created_at=utcnow() - timedelta(days=9),
        ),
        Announcement(
            title="Welcome to the Fall 2026 Semester",
            body="Welcome back! Classes for Fall 2026 have commenced. Please verify your enrolled "
                 "courses on the portal and report any discrepancy to the department office.",
            created_at=utcnow() - timedelta(days=100),
        ),
        Announcement(
            title="Department-Wise Project Exhibitions",
            body="Each department will hold a project exhibition in the last week of the semester. "
                 "Final year students must register their projects with their department heads by the end of this month.",
            expires_on=days_ahead(30),
            created_at=utcnow() - timedelta(days=3),
        ),
        Announcement(
            title="Campus Surveillance System Upgrade",
            body="The CampusGuard AI surveillance system will be upgraded this weekend. "
                 "All students are reminded to carry their ID cards at all times to avoid false alerts.",
            created_at=utcnow() - timedelta(days=1),
        ),
    ])

    db.session.commit()


def print_summary():
    counts = {
        "Students": Student.query.count(),
        "Teachers": Teacher.query.count(),
        "Courses": Course.query.count(),
        "Enrollments": Enrollment.query.count(),
        "Attendance records": Attendance.query.count(),
        "Assignments": Assignment.query.count(),
        "Submissions": Submission.query.count(),
        "Assessments": Assessment.query.count(),
        "Marks": Mark.query.count(),
        "Finalized results": CourseResult.query.filter_by(is_finalized=True).count(),
        "Challans": Challan.query.count(),
        "Warnings": Warning.query.count(),
        "Announcements": Announcement.query.count(),
    }

    print()
    print("=" * 64)
    print("  LMS demo data seeded successfully")
    print("=" * 64)
    print()
    print("  Login credentials")
    print("  " + "-" * 60)
    print(f"  {'Role':<10}{'Email':<36}{'Password'}")
    print(f"  {'Admin':<10}{'admin@university.edu.pk':<36}{'admin123'}")
    print(f"  {'Student':<10}{'<roll_no>@university.edu.pk':<36}{'student123'}")
    print(f"  {'Teacher':<10}{'<name>@university.edu.pk':<36}{'teacher123'}")
    print()
    print("  Teacher credentials by department")
    print("  " + "-" * 60)
    for dept in DEPARTMENTS:
        dept_teachers = Teacher.query.filter_by(department=dept).all()
        if dept_teachers:
            print(f"\n  [{dept}]")
            for t in dept_teachers:
                print(f"    {t.user.email:<40} teacher123  ({t.employee_id})")
    print()
    print("  Department breakdown")
    print("  " + "-" * 60)
    for dept in DEPARTMENTS:
        s_count = Student.query.filter_by(program=dept).count()
        c_count = Course.query.filter_by(department=dept).count()
        t_count = Teacher.query.filter_by(department=dept).count()
        print(f"  {dept:<12} {t_count} teachers, {s_count} students, {c_count} courses")
    print()
    print("  CampusGuard AI students")
    print("  " + "-" * 60)
    for roll in ["SE-001", "SE-002", "SE-003"]:
        st = Student.query.filter_by(roll_no=roll).first()
        if st:
            print(f"  {st.roll_no:<12}{st.user.email:<36}student123")
    print()
    print("  Generated data")
    print("  " + "-" * 60)
    for label, value in counts.items():
        print(f"  {label:<22}{value}")
    print()
    print("  All dates are relative to today, so overdue/due-soon states")
    print("  stay correct on any run date.")
    print()


def main():
    parser = argparse.ArgumentParser(description="Seed the LMS demo database.")
    parser.add_argument("--reset", action="store_true",
                        help="drop all tables, clear uploads, and reseed from scratch")
    args = parser.parse_args()

    with app.app_context():
        if args.reset:
            reset_database()
        elif User.query.count() > 0:
            print("Database already contains data. Use --reset to wipe and reseed.")
            return
        seed()
        print_summary()


if __name__ == "__main__":
    main()
