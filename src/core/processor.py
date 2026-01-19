"""
Data Processor and Output Handler
Formats and outputs event data to terminal and files
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and output FourMeme events"""

    def __init__(self, output_dir: str = "data/events"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Current output file
        self.current_file = None
        self.current_date = None

        # Statistics
        self.events_saved = 0
        self.events_by_type = {
            'TokenLaunched': 0,
            'BondingProgress': 0,
            'TokenGraduated': 0,
            'TokenPurchase': 0
        }

    def _get_output_file(self) -> Path:
        """Get output file for current date (auto-rotate daily)"""
        today = datetime.now().strftime('%Y%m%d')

        if today != self.current_date:
            self.current_date = today
            self.current_file = self.output_dir / f"fourmeme_events_{today}.jsonl"
            logger.info(f"Output file: {self.current_file}")

        return self.current_file

    async def process_event(self, event_name: str, event_data: Dict):
        """Process an event: format, print, and save"""
        try:
            # Format event data
            formatted = await self._format_event(event_name, event_data)

            # Print to terminal
            self._print_event(event_name, formatted)

            # Save to file
            await self._save_event(event_name, formatted)

            # Update statistics
            self.events_by_type[event_name] = self.events_by_type.get(event_name, 0) + 1
            self.events_saved += 1

        except Exception as e:
            logger.error(f"Error processing event {event_name}: {e}")

    async def _format_event(self, event_name: str, event_data: Dict) -> Dict:
        """Format raw event data into structured format"""
        timestamp = event_data.get('timestamp', int(datetime.now().timestamp()))
        block_number = event_data.get('blockNumber', 0)
        tx_hash = event_data.get('transactionHash', b'').hex()

        # Base structure
        formatted = {
            'event_type': self._event_type_map(event_name),
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat(),
            'block_number': block_number,
            'tx_hash': tx_hash,
        }

        # Extract event-specific data
        args = event_data.get('args', {})

        if event_name == 'TokenLaunched':
            formatted.update({
                'token_address': args.get('token', ''),
                'token_name': args.get('name', 'Unknown'),
                'token_symbol': args.get('symbol', 'Unknown'),
                'creator': args.get('creator', ''),
                'initial_liquidity': float(args.get('initialLiquidity', 0)) / 1e18,  # Wei to BNB
            })

        elif event_name == 'BondingProgress':
            formatted.update({
                'token_address': args.get('token', ''),
                'bonding_progress': float(args.get('progress', 0)) / 100,  # Assuming basis points
                'market_cap': float(args.get('currentMarketCap', 0)) / 1e18,
            })

        elif event_name == 'TokenGraduated':
            formatted.update({
                'token_address': args.get('token', ''),
                'final_market_cap': float(args.get('finalMarketCap', 0)) / 1e18,
                'dex_pair': args.get('dexPair', ''),
            })

        elif event_name == 'TokenPurchase':
            formatted.update({
                'token_address': args.get('token', ''),
                'user': args.get('user', ''),
                'bnb_amount': float(args.get('bnbAmount', 0)) / 1e18,
                'token_amount': float(args.get('tokenAmount', 0)) / 1e18,
            })

        return formatted

    def _event_type_map(self, event_name: str) -> str:
        """Map event names to simplified types"""
        mapping = {
            'TokenLaunched': 'launch',
            'BondingProgress': 'boost',
            'TokenGraduated': 'graduate',
            'TokenPurchase': 'purchase'
        }
        return mapping.get(event_name, 'unknown')

    def _print_event(self, event_name: str, data: Dict):
        """Print formatted event to terminal with colors"""
        timestamp = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

        # Event type with emoji and color
        event_styles = {
            'launch': (Fore.GREEN + '🚀 LAUNCH', Style.RESET_ALL),
            'boost': (Fore.YELLOW + '📈 BOOST ', Style.RESET_ALL),
            'graduate': (Fore.CYAN + '🎓 GRADUATE', Style.RESET_ALL),
            'purchase': (Fore.BLUE + '💰 PURCHASE', Style.RESET_ALL),
        }

        event_type = data['event_type']
        emoji_prefix, reset = event_styles.get(event_type, (Fore.WHITE + '📍 EVENT', Style.RESET_ALL))

        # Build output string based on event type
        if event_type == 'launch':
            output = (
                f"[{timestamp}] {emoji_prefix}{reset} | "
                f"{Fore.MAGENTA}${data.get('token_symbol', 'N/A')}{reset} "
                f"({data.get('token_name', 'N/A')}) | "
                f"{data.get('token_address', '')[:10]}... | "
                f"{Fore.GREEN}{data.get('initial_liquidity', 0):.2f} BNB{reset}"
            )

        elif event_type == 'boost':
            output = (
                f"[{timestamp}] {emoji_prefix}{reset} | "
                f"{data.get('token_address', '')[:10]}... | "
                f"Progress: {Fore.YELLOW}{data.get('bonding_progress', 0):.1f}%{reset} | "
                f"MCap: ${data.get('market_cap', 0):.2f}"
            )

        elif event_type == 'graduate':
            output = (
                f"[{timestamp}] {emoji_prefix}{reset} | "
                f"{data.get('token_address', '')[:10]}... | "
                f"Final MCap: {Fore.CYAN}${data.get('final_market_cap', 0):,.0f}{reset} | "
                f"DEX: {data.get('dex_pair', '')[:10]}..."
            )

        elif event_type == 'purchase':
            output = (
                f"[{timestamp}] {emoji_prefix}{reset} | "
                f"{data.get('token_address', '')[:10]}... | "
                f"User: {data.get('user', '')[:10]}... | "
                f"{Fore.GREEN}{data.get('bnb_amount', 0):.3f} BNB{reset} → "
                f"{data.get('token_amount', 0):,.0f} tokens"
            )

        else:
            output = f"[{timestamp}] {emoji_prefix}{reset} | {json.dumps(data)}"

        print(output)

    async def _save_event(self, event_name: str, data: Dict):
        """Save event to JSONL file"""
        try:
            output_file = self._get_output_file()

            # Append to file (one JSON per line)
            with output_file.open('a', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            logger.error(f"Failed to save event to file: {e}")

            # Try to save to error log
            error_file = self.output_dir / "error_events.jsonl"
            try:
                with error_file.open('a', encoding='utf-8') as f:
                    json.dump({
                        'error': str(e),
                        'event_name': event_name,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }, f)
                    f.write('\n')
            except Exception as err:
                logger.critical(f"Failed to save to error log: {err}")

    def print_stats(self):
        """Print statistics"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Statistics:{Style.RESET_ALL}")
        print(f"  Total events processed: {Fore.GREEN}{self.events_saved}{Style.RESET_ALL}")
        for event_type, count in self.events_by_type.items():
            if count > 0:
                print(f"    {event_type}: {count}")
        print(f"  Output directory: {self.output_dir}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

    def get_stats(self) -> Dict:
        """Get processor statistics"""
        return {
            'total_events': self.events_saved,
            'events_by_type': self.events_by_type.copy(),
            'output_dir': str(self.output_dir),
            'current_file': str(self.current_file) if self.current_file else None
        }
