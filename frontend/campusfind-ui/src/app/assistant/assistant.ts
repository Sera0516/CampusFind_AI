
import {
  Component,
  inject,
  ChangeDetectorRef
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  AssistantService,
  AssistantResponse
} from '../services/assistant.service';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  reports?: AssistantResponse['retrieved_reports'];
}

@Component({
  selector: 'app-assistant',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './assistant.html',
  styleUrl: './assistant.css'
})
export class Assistant {

  private readonly assistantService = inject(AssistantService);
  private readonly cdr = inject(ChangeDetectorRef);

  question = '';
  loading = false;
  error = '';

  messages: ChatMessage[] = [];

  // Safely format Gemini Markdown responses
  formatAnswer(text: string): string {

    const escapeHtml = (value: string): string =>
      value.replace(/[&<>"']/g, char => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      })[char]!);

    return escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  }

  // Ask CampusFind AI
  askQuestion(): void {

    const question = this.question.trim();

    if (
      question.length < 3 ||
      question.length > 1000 ||
      this.loading
    ) {
      return;
    }

    this.messages.push({
      role: 'user',
      content: question
    });

    this.question = '';
    this.loading = true;
    this.error = '';

    this.cdr.detectChanges();

    this.assistantService.ask(question).subscribe({

      next: (response: AssistantResponse) => {

        console.log('CampusFind AI response:', response);

        this.messages.push({
          role: 'assistant',
          content: response.answer,
          reports: response.retrieved_reports ?? []
        });

        this.loading = false;
        this.cdr.detectChanges();
      },

      error: (err) => {

        console.error('CampusFind AI error:', err);

        this.error =
          err.error?.detail ||
          'Unable to reach the AI assistant. Please try again.';

        this.loading = false;
        this.cdr.detectChanges();
      },

      complete: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  // Handle suggested questions
  useSuggestion(question: string): void {
    this.question = question;
    this.askQuestion();
  }
}
