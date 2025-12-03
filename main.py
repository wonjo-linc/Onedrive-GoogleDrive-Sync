"""
Main entry point for OneDrive-GoogleDrive Sync
"""

import argparse
import sys
from src.sync.sync_engine import SyncEngine


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="OneDrive-GoogleDrive Sync - Bidirectional file synchronization"
    )
    
    parser.add_argument(
        '--source',
        choices=['onedrive', 'gdrive'],
        help='Source platform (onedrive or gdrive)'
    )
    
    parser.add_argument(
        '--target',
        choices=['onedrive', 'gdrive'],
        help='Target platform (onedrive or gdrive)'
    )
    
    parser.add_argument(
        '--bidirectional',
        action='store_true',
        help='Perform bidirectional sync'
    )
    
    parser.add_argument(
        '--folder',
        type=str,
        help='Specific folder to sync (optional)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.bidirectional and (not args.source or not args.target):
        parser.error("Either --bidirectional or both --source and --target must be specified")
    
    if args.source == args.target:
        parser.error("Source and target must be different platforms")
    
    # Initialize sync engine
    try:
        engine = SyncEngine()
        
        if args.bidirectional:
            engine.bidirectional_sync(args.folder)
        elif args.source == 'onedrive' and args.target == 'gdrive':
            engine.sync_onedrive_to_gdrive(args.folder)
        elif args.source == 'gdrive' and args.target == 'onedrive':
            engine.sync_gdrive_to_onedrive(args.folder)
        
        print("\n✓ Synchronization completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
