export interface ServerEvent {
  id: string;
  data: string;
}

/** Incremental UTF-8 decoding belongs to the caller; frames may span arbitrary network chunks. */
export class SseParser {
  private buffer = '';
  private id = '';
  private data: string[] = [];

  push(chunk: string): ServerEvent[] {
    this.buffer += chunk;
    if (this.buffer.length > 65536) throw new Error('event_too_large');
    const events: ServerEvent[] = [];
    let newline: number;
    while ((newline = this.buffer.indexOf('\n')) !== -1) {
      const line = this.buffer.slice(0, newline).replace(/\r$/, '');
      this.buffer = this.buffer.slice(newline + 1);
      if (!line) {
        if (this.data.length) events.push({ id: this.id, data: this.data.join('\n') });
        this.data = [];
      } else if (line.startsWith('id:')) {
        this.id = line.slice(3).replace(/^ /, '');
      } else if (line.startsWith('data:')) {
        this.data.push(line.slice(5).replace(/^ /, ''));
        if (this.data.join('\n').length > 65536) throw new Error('event_too_large');
      }
    }
    return events;
  }
}
