#include "Fast3DView.h"
#include <QOpenGLFunctions>
void Fast3DView::initializeGL(){ initializeOpenGLFunctions(); glClearColor(0.04f,0.05f,0.07f,1.0f); }
void Fast3DView::resizeGL(int w,int h){ glViewport(0,0,w,h); }
void Fast3DView::paintGL(){ glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT); }
