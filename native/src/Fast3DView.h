#pragma once
#include <QOpenGLWidget>
#include <QOpenGLFunctions>
class Fast3DView : public QOpenGLWidget, protected QOpenGLFunctions {
    Q_OBJECT
public:
    explicit Fast3DView(QWidget* p=nullptr):QOpenGLWidget(p){}
protected:
    void initializeGL() override;
    void resizeGL(int w,int h) override;
    void paintGL() override;
};
