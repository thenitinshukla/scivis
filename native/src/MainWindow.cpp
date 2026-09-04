#include "MainWindow.h"
#include "Fast3DView.h"
#include <QTabWidget>
#include <QLabel>
MainWindow::MainWindow(){
    setWindowTitle("Scientific Simulation Platform - Native Qt Renderer"); resize(1440,900);
    auto* tabs=new QTabWidget(this); setCentralWidget(tabs);
    tabs->addTab(new Fast3DView(this),"GPU 3D");
    tabs->addTab(new QLabel("Native Qt/OpenGL data pipeline. Connect this view to HDF5/VTK backends in the production C++ build."),"Architecture");
}
