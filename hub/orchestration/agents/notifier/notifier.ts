import axios from 'axios';
import { Input, Output } from './schemas';

export class Notifier {
  async send(input: Input): Promise<Output> {
    const timestamp = new Date().toISOString();

    try {
      switch (input.channel) {
        case 'slack':
          return await this.sendSlack(input, timestamp);
        case 'discord':
          return await this.sendDiscord(input, timestamp);
        case 'console':
          return this.sendConsole(input, timestamp);
        default:
          throw new Error(`Unknown channel: ${input.channel}`);
      }
    } catch (error: any) {
      return {
        success: false,
        channel: input.channel,
        timestamp,
        error: error.message,
      };
    }
  }

  private async sendSlack(input: Input, timestamp: string): Promise<Output> {
    if (!input.webhookUrl) {
      throw new Error('webhookUrl required for Slack');
    }

    const color = this.getSeverityColor(input.severity);
    const payload = {
      attachments: [
        {
          color,
          title: `${this.getSeverityEmoji(input.severity)} ${input.severity.toUpperCase()}`,
          text: input.message,
          fields: input.metadata
            ? Object.entries(input.metadata).map(([key, value]) => ({
                title: key,
                value: String(value),
                short: true,
              }))
            : [],
          ts: Math.floor(Date.now() / 1000),
        },
      ],
    };

    const response = await axios.post(input.webhookUrl, payload);

    return {
      success: response.status === 200,
      channel: 'slack',
      messageId: (response.data as any).ts,
      timestamp,
    };
  }

  private async sendDiscord(input: Input, timestamp: string): Promise<Output> {
    if (!input.webhookUrl) {
      throw new Error('webhookUrl required for Discord');
    }

    const color = this.getSeverityColorInt(input.severity);
    const payload = {
      embeds: [
        {
          title: `${this.getSeverityEmoji(input.severity)} ${input.severity.toUpperCase()}`,
          description: input.message,
          color,
          fields: input.metadata
            ? Object.entries(input.metadata).map(([key, value]) => ({
                name: key,
                value: String(value),
                inline: true,
              }))
            : [],
          timestamp,
        },
      ],
    };

    const response = await axios.post(input.webhookUrl, payload);

    return {
      success: response.status === 204,
      channel: 'discord',
      messageId: response.headers['x-message-id'],
      timestamp,
    };
  }

  private sendConsole(input: Input, timestamp: string): Output {
    const emoji = this.getSeverityEmoji(input.severity);
    // Use stderr for console output to keep stdout pure for JSON
    console.error(`\n${emoji} [${input.severity.toUpperCase()}] ${input.message}`);

    if (input.metadata) {
      console.error('Metadata:', JSON.stringify(input.metadata, null, 2));
    }

    return {
      success: true,
      channel: 'console',
      timestamp,
    };
  }

  private getSeverityColor(severity: string): string {
    const colors: Record<string, string> = {
      info: '#36a64f',
      warning: '#ff9900',
      error: '#ff0000',
      critical: '#8b0000',
    };
    return colors[severity] || '#cccccc';
  }

  private getSeverityColorInt(severity: string): number {
    const colors: Record<string, number> = {
      info: 0x36a64f,
      warning: 0xff9900,
      error: 0xff0000,
      critical: 0x8b0000,
    };
    return colors[severity] || 0xcccccc;
  }

  private getSeverityEmoji(severity: string): string {
    const emojis: Record<string, string> = {
      info: 'ℹ️',
      warning: '⚠️',
      error: '❌',
      critical: '🚨',
    };
    return emojis[severity] || '📢';
  }
}
