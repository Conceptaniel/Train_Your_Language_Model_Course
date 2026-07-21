from pathlib import Path

infile = Path('data') / 'dm_bpe.txt'
outdir = Path('output')
outdir.mkdir(parents=True, exist_ok=True)
outfile = outdir / 'combined_text.txt'

text = infile.read_text(encoding='utf-8', errors='replace')
# join lines with a space to create a single long sequence
text_sequence = ' '.join(line.strip() for line in text.splitlines() if line.strip())
outfile.write_text(text_sequence, encoding='utf-8')
print(f'Wrote {outfile} (chars: {len(text_sequence)})')
