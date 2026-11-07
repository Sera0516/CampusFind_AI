import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReceivedClaims } from './received-claims';

describe('ReceivedClaims', () => {
  let component: ReceivedClaims;
  let fixture: ComponentFixture<ReceivedClaims>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReceivedClaims],
    }).compileComponents();

    fixture = TestBed.createComponent(ReceivedClaims);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
