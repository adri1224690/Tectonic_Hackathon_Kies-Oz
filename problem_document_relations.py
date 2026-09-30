import json

RELATIONS_FILE = "mockproblemDocumentRelations.json"
DOCUMENTS_FILE = "mockDocumentDB.json"
PROBLEMS_FILE = "mockProblemsDB.json"


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


# --------------------------------------------------
# GET RELATIONSHIPS
# --------------------------------------------------

def get_relations_for_problem(problem_id):
    data = load_json(RELATIONS_FILE)

    return [
        relation
        for relation in data["problem_document_relations"]
        if relation["problem_id"] == problem_id
    ]


def get_relations_for_document(document_id):
    data = load_json(RELATIONS_FILE)

    return [
        relation
        for relation in data["problem_document_relations"]
        if relation["document_id"] == document_id
    ]


# --------------------------------------------------
# GET FULL DOCUMENT INFORMATION
# --------------------------------------------------

def get_documents_for_problem(problem_id):

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
# DOCUMENT STATISTICS
# --------------------------------------------------

def get_document_stats(document_id):

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
    else:
        helpful_rate = 0

    return {
        "document_id": document_id,
        "times_used": total_uses,
        "times_helpful": helpful_uses,
        "times_primary_source": primary_uses,
        "helpful_rate": round(helpful_rate, 1)
    }


# --------------------------------------------------
# ADD NEW RELATIONSHIP
# --------------------------------------------------

def add_relation(
    problem_id,
    document_id,
    helpful,
    primary_source
):

    data = load_json(RELATIONS_FILE)

    new_relation = {
        "problem_id": problem_id,
        "document_id": document_id,
        "used": True,
        "helpful": helpful,
        "primary_source": primary_source
    }

    data["problem_document_relations"].append(
        new_relation
    )

    save_json(
        RELATIONS_FILE,
        data
    )

    print(
        f"Added relationship: "
        f"{problem_id} -> {document_id}"
    )


# --------------------------------------------------
# DEMO
# --------------------------------------------------

if __name__ == "__main__":

    print("\n==============================")
    print(" PROBLEM -> DOCUMENT DEMO")
    print("==============================")

    problem_id = "case-006"

    print(
        f"\nDocuments used for {problem_id}:\n"
    )

    results = get_documents_for_problem(
        problem_id
    )

    for result in results:

        document = result["document"]
        relationship = result["relationship"]

        print(
            f"Document: {document['title']}"
        )

        print(
            f"ID: {document['id']}"
        )

        print(
            f"Helpful: {relationship['helpful']}"
        )

        print(
            f"Primary source: "
            f"{relationship['primary_source']}"
        )

        print("------------------------------")

    print("\nDocument statistics:\n")

    stats = get_document_stats("doc-006")

    print(
        json.dumps(
            stats,
            indent=2
        )
    )