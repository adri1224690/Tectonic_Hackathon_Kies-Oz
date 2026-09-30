import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RELATIONS_FILE = "mockproblemDocumentRelations.json"
DOCUMENTS_FILE = "mockDocumentDB.json"
PROBLEMS_FILE = "mockProblemsDB.json"


# --------------------------------------------------
# JSON HELPERS
# --------------------------------------------------

def load_json(filename):
    safe_filename = os.path.basename(filename)
    safe_path = os.path.join(BASE_DIR, safe_filename)

    with open(safe_path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_json(filename, data):
    safe_filename = os.path.basename(filename)
    safe_path = os.path.join(BASE_DIR, safe_filename)

    with open(safe_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


# --------------------------------------------------
# GET RELATIONSHIPS
# --------------------------------------------------

def get_relations_for_problem(problem_id):
    """Return all document relationships for a problem."""

    data = load_json(RELATIONS_FILE)

    return [
        relation
        for relation in data["problem_document_relations"]
        if relation["problem_id"] == problem_id
    ]


def get_relations_for_document(document_id):
    """Return all problem relationships for a document."""

    data = load_json(RELATIONS_FILE)

    return [
        relation
        for relation in data["problem_document_relations"]
        if relation["document_id"] == document_id
    ]


# --------------------------------------------------
# PROBLEM -> DOCUMENTS
# --------------------------------------------------

def get_documents_for_problem(problem_id):
    """
    Return the full document information for all documents
    that were used for a specific problem.
    """

    relations = get_relations_for_problem(problem_id)

    document_data = load_json(DOCUMENTS_FILE)
    documents = document_data["documents"]

    results = []

    for relation in relations:

        document = next(
            (
                doc
                for doc in documents
                if doc["id"] == relation["document_id"]
            ),
            None
        )

        if document:
            results.append({
                "document": document,
                "relationship": relation
            })

    return results


# --------------------------------------------------
# DOCUMENT -> PROBLEMS
# --------------------------------------------------

def get_problems_for_document(document_id):
    """
    Return the full problem information for all problems
    where a specific document was used.
    """

    relations = get_relations_for_document(document_id)

    problem_data = load_json(PROBLEMS_FILE)
    problems = problem_data["cases"]

    results = []

    for relation in relations:

        problem = next(
            (
                problem
                for problem in problems
                if problem["id"] == relation["problem_id"]
            ),
            None
        )

        if problem:
            results.append({
                "problem": problem,
                "relationship": relation
            })

    return results


# --------------------------------------------------
# DOCUMENT STATISTICS
# --------------------------------------------------

def get_document_stats(document_id):
    """
    Calculate historical usage statistics for a document.
    """

    relations = get_relations_for_document(document_id)

    total_uses = len(relations)

    helpful_uses = sum(
        1
        for relation in relations
        if relation["helpful"]
    )

    primary_uses = sum(
        1
        for relation in relations
        if relation["primary_source"]
    )

    if total_uses > 0:
        helpful_rate = helpful_uses / total_uses * 100
        primary_rate = primary_uses / total_uses * 100
    else:
        helpful_rate = 0
        primary_rate = 0

    return {
        "document_id": document_id,
        "times_used": total_uses,
        "times_helpful": helpful_uses,
        "times_primary_source": primary_uses,
        "helpful_rate": round(helpful_rate, 1),
        "primary_rate": round(primary_rate, 1)
    }


# --------------------------------------------------
# ADD OR UPDATE RELATIONSHIP
# --------------------------------------------------

def add_relation(
    problem_id,
    document_id,
    helpful,
    primary_source
):
    """
    Add a new problem-document relationship.

    If the relationship already exists,
    update it instead of creating a duplicate.
    """

    data = load_json(RELATIONS_FILE)
    relations = data["problem_document_relations"]

    # Check if relationship already exists
    for relation in relations:

        if (
            relation["problem_id"] == problem_id
            and relation["document_id"] == document_id
        ):
            relation["used"] = True
            relation["helpful"] = helpful
            relation["primary_source"] = primary_source

            save_json(RELATIONS_FILE, data)

            print(
                f"Updated existing relationship: "
                f"{problem_id} -> {document_id}"
            )

            return relation

    # Relationship does not exist yet
    new_relation = {
        "problem_id": problem_id,
        "document_id": document_id,
        "used": True,
        "helpful": helpful,
        "primary_source": primary_source
    }

    relations.append(new_relation)

    save_json(RELATIONS_FILE, data)

    print(
        f"Added new relationship: "
        f"{problem_id} -> {document_id}"
    )

    return new_relation


# --------------------------------------------------
# DEMO
# --------------------------------------------------

if __name__ == "__main__":

    print("\n==============================")
    print(" PROBLEM -> DOCUMENT DEMO")
    print("==============================")

    problem_id = "case-006"

    print(f"\nDocuments used for {problem_id}:\n")

    results = get_documents_for_problem(problem_id)

    for result in results:

        document = result["document"]
        relationship = result["relationship"]

        print(f"Document: {document['title']}")
        print(f"ID: {document['id']}")
        print(f"Helpful: {relationship['helpful']}")
        print(
            f"Primary source: "
            f"{relationship['primary_source']}"
        )
        print("------------------------------")

    print("\n==============================")
    print(" DOCUMENT -> PROBLEM DEMO")
    print("==============================")

    document_id = "doc-006"

    print(f"\nProblems where {document_id} was used:\n")

    problems = get_problems_for_document(document_id)

    for result in problems:

        problem = result["problem"]
        relationship = result["relationship"]

        print(f"Problem: {problem['title']}")
        print(f"ID: {problem['id']}")
        print(f"Helpful: {relationship['helpful']}")
        print(
            f"Primary source: "
            f"{relationship['primary_source']}"
        )
        print("------------------------------")

    print("\n==============================")
    print(" DOCUMENT STATISTICS")
    print("==============================")

    stats = get_document_stats(document_id)

    print(
        json.dumps(
            stats,
            indent=2
        )
    )