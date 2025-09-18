#!/usr/bin/env python3
"""
Script to explore ACL Anthology library capabilities
"""

from acl_anthology import Anthology
import time

print("Loading ACL Anthology data...")
start_time = time.time()

# Load the anthology
anthology = Anthology.from_repo()

load_time = time.time() - start_time
print(f"Loaded in {load_time:.2f} seconds")

# Get basic statistics
papers_gen = anthology.papers()
papers_list = list(papers_gen)
print(f"Total papers: {len(papers_list)}")

# Explore a sample paper
sample_paper = papers_list[0]
sample_id = sample_paper.id

print(f"\nSample paper ID: {sample_id}")
print(f"Title: {sample_paper.title}")
print(f"Authors: {[author.name for author in sample_paper.authors]}")

# Print available attributes/methods
print(f"\nPaper attributes:")
for attr in dir(sample_paper):
    if not attr.startswith('_'):
        try:
            value = getattr(sample_paper, attr)
            if not callable(value):
                print(f"  {attr}: {type(value)} - {value}")
        except:
            print(f"  {attr}: (error accessing)")

# Test search functionality
print(f"\nTesting search for 'attention'...")
attention_papers = []
for paper in papers_list:
    if 'attention' in str(paper.title).lower():
        attention_papers.append(paper)
        if len(attention_papers) >= 5:
            break

print(f"Found {len(attention_papers)} sample papers with 'attention' in title:")
for paper in attention_papers:
    print(f"  {paper.id}: {paper.title}")

# Test finding people
print(f"\nTesting people search...")
try:
    people = anthology.find_people("Bengio")
    print(f"Found {len(people)} people with 'Bengio':")
    for person in people[:5]:
        print(f"  {person.name}")
except Exception as e:
    print(f"People search error: {e}")