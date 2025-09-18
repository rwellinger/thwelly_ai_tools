import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageDetailPanelComponent } from './image-detail-panel.component';

describe('ImageDetailPanelComponent', () => {
  let component: ImageDetailPanelComponent;
  let fixture: ComponentFixture<ImageDetailPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImageDetailPanelComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ImageDetailPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
