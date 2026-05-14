import argparse
import json

from src.blockchain import solana
from src.blockchain import arweave

# ============================================================
# Facade for backend usage
# ============================================================

# Solana functions
upload = solana.upload
upload_string = solana.upload_string
download = solana.download
download_by_signatures = solana.download_by_signatures

# Arweave functions
ar_upload = arweave.ar_upload
ar_upload_string = arweave.ar_upload_string
ar_download = arweave.ar_download
ar_download_by_tx_ids = arweave.ar_download_by_tx_ids

# ============================================================
# CLI Entry Point
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Digital Tattoo Tool (Solana / Arweave)")
    parser.add_argument("action", choices=["upload", "upload_string", "download", "read", "list", "balance"], help="Action to execute")
    parser.add_argument("--file", help="File path (for upload or download destination)")
    parser.add_argument("--string", help="String to tattoo")
    parser.add_argument("--id", help="Unique tattoo ID")
    parser.add_argument("--email", help="User Email")
    parser.add_argument("--blockchain", choices=["solana", "arweave"], default="solana", help="Blockchain to use (default: solana)")
    parser.add_argument("--tags", help='Extra Arweave tags in JSON format, e.g. \'{"Project": "MyApp", "Version": "1.0"}\'')
    args = parser.parse_args()

    # Parse optional extra tags
    extra_tags = None
    if args.tags:
        try:
            extra_tags = json.loads(args.tags)
            if not isinstance(extra_tags, dict):
                print("Error: --tags must be a JSON object (dict), e.g. '{\"Key\": \"Value\"}'")
                extra_tags = None
            else:
                print(f"Extra tags loaded: {extra_tags}")
        except json.JSONDecodeError as e:
            print(f"Error parsing --tags JSON: {e}")
            extra_tags = None

    use_arweave = (args.blockchain == "arweave")

    if args.action == "upload":
        if not args.file or not args.id or not args.email:
            print("File upload requires --file, --id and --email")
        elif use_arweave:
            arweave.ar_check_balance()
            arweave.ar_upload(args.file, args.id, args.email, extra_tags)
        else:
            solana.check_balances()
            solana.upload(args.file, args.id, args.email)
    elif args.action == "upload_string":
        if not args.string or not args.id or not args.email:
            print("String upload requires --string, --id and --email")
        elif use_arweave:
            arweave.ar_check_balance()
            arweave.ar_upload_string(args.string, args.id, args.email, extra_tags)
        else:
            solana.check_balances()
            solana.upload_string(args.string, args.id, args.email)
    elif args.action == "download":
        if not args.file or not args.id or not args.email:
            print("Download requires --file, --id and --email")
        elif use_arweave:
            arweave.ar_download(args.id, args.file, args.email)
        else:
            solana.download(args.id, args.file, args.email)
    elif args.action == "read":
        if not args.id or not args.email:
            print("Read requires --id and --email")
        elif use_arweave:
            arweave.ar_download(args.id, None, args.email)
        else:
            solana.download(args.id, None, args.email)
    elif args.action == "list":
        if not args.email:
            print("List requires --email")
        elif use_arweave:
            arweave.ar_list_tattoos(args.email)
        else:
            solana.list_tattoos(args.email)
    elif args.action == "balance":
        if use_arweave:
            arweave.ar_check_balance()
        else:
            solana.check_balances()
