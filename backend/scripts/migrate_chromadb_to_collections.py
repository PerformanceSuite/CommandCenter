"""
Migrate existing ChromaDB data to per-repository collections.

This script:
1. Reads from old single collection (or default collection)
2. Migrates documents to repository-specific collections based on metadata
3. Creates default repository collection for documents without repository_id

Usage:
    python backend/scripts/migrate_chromadb_to_collections.py

Note: This script is safe to run multiple times - it won't duplicate data.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ERROR: ChromaDB not installed. Run: pip install chromadb")
    sys.exit(1)


def migrate_to_repository_collections(
    db_path: str = "./rag_storage",
    old_collection_name: str = "knowledge_default",
    default_repository_id: int = 1
):
    """
    Migrate documents from old collection to repository-specific collections.

    Args:
        db_path: Path to ChromaDB storage directory
        old_collection_name: Name of the old collection to migrate from
        default_repository_id: Default repository ID for documents without metadata
    """
    print("=" * 60)
    print("ChromaDB Collection Migration Script")
    print("=" * 60)
    print(f"Database path: {db_path}")
    print(f"Old collection: {old_collection_name}")
    print(f"Default repository ID: {default_repository_id}")
    print()

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=db_path)

    # List existing collections
    existing_collections = client.list_collections()
    print(f"Found {len(existing_collections)} existing collections:")
    for col in existing_collections:
        print(f"  - {col.name} ({col.count()} documents)")
    print()

    # Try to get old collection
    try:
        old_collection = client.get_collection(name=old_collection_name)
        print(f"Found old collection '{old_collection_name}' with {old_collection.count()} documents")
    except Exception as e:
        print(f"No old collection found: {e}")
        print("Nothing to migrate. This is fine if you're starting fresh.")
        return

    # Get all documents from old collection
    all_docs = old_collection.get()

    if not all_docs or not all_docs.get('ids'):
        print("No documents to migrate")
        return

    total_docs = len(all_docs['ids'])
    print(f"\nMigrating {total_docs} documents...")
    print()

    # Group documents by repository_id
    docs_by_repo = {}

    for i, doc_id in enumerate(all_docs['ids']):
        metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') else {}
        document = all_docs['documents'][i] if all_docs.get('documents') else ""

        # Get repository_id from metadata, or use default
        repo_id = metadata.get('repository_id', default_repository_id)

        if repo_id not in docs_by_repo:
            docs_by_repo[repo_id] = {
                'ids': [],
                'documents': [],
                'metadatas': []
            }

        docs_by_repo[repo_id]['ids'].append(doc_id)
        docs_by_repo[repo_id]['documents'].append(document)
        docs_by_repo[repo_id]['metadatas'].append(metadata)

    # Create repository-specific collections and migrate data
    print(f"Found documents for {len(docs_by_repo)} repositories")
    print()

    for repo_id, docs in docs_by_repo.items():
        collection_name = f"knowledge_repo_{repo_id}"
        doc_count = len(docs['ids'])

        print(f"Processing repository {repo_id}:")
        print(f"  - Collection: {collection_name}")
        print(f"  - Documents: {doc_count}")

        try:
            # Get or create collection
            try:
                collection = client.get_collection(name=collection_name)
                print(f"  - Using existing collection (had {collection.count()} documents)")
            except:
                collection = client.create_collection(
                    name=collection_name,
                    metadata={
                        "repository_id": repo_id,
                        "migrated_from": old_collection_name
                    }
                )
                print(f"  - Created new collection")

            # Add documents to repository collection
            # Use upsert to avoid duplicates if run multiple times
            collection.upsert(
                ids=docs['ids'],
                documents=docs['documents'],
                metadatas=docs['metadatas']
            )

            print(f"  - Migrated {doc_count} documents")
            print(f"  - Collection now has {collection.count()} documents")
            print()

        except Exception as e:
            print(f"  - ERROR: Failed to migrate: {e}")
            print()

    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)

    # Show final state
    all_collections = client.list_collections()
    print(f"Total collections: {len(all_collections)}")
    print()

    for col in all_collections:
        print(f"{col.name}:")
        print(f"  - Documents: {col.count()}")
        print(f"  - Metadata: {col.metadata}")
        print()

    print("=" * 60)
    print("Migration completed successfully!")
    print()
    print("NEXT STEPS:")
    print("1. Verify the migration by checking collection counts above")
    print("2. Test queries with repository_id parameter")
    print(f"3. Once verified, you can delete the old '{old_collection_name}' collection:")
    print(f"   >>> client.delete_collection('{old_collection_name}')")
    print("=" * 60)


def main():
    """Main entry point for migration script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate ChromaDB to per-repository collections"
    )
    parser.add_argument(
        "--db-path",
        default="./rag_storage",
        help="Path to ChromaDB storage directory (default: ./rag_storage)"
    )
    parser.add_argument(
        "--old-collection",
        default="knowledge_default",
        help="Name of old collection to migrate from (default: knowledge_default)"
    )
    parser.add_argument(
        "--default-repo-id",
        type=int,
        default=1,
        help="Default repository ID for documents without metadata (default: 1)"
    )

    args = parser.parse_args()

    try:
        migrate_to_repository_collections(
            db_path=args.db_path,
            old_collection_name=args.old_collection,
            default_repository_id=args.default_repo_id
        )
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
