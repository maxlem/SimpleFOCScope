import QtQuick 2.9
import QtQuick.Controls 2.1
import QtCharts 2.1
import QtQuick.Layouts 1.15

import SimpleFOC 1.0

ApplicationWindow
{
    width: 800
    height: 600

    SimpleFOCSerialScope
    {
        id: scope_

        traces : SimpleFOCScope
        {
            id: ds_
            chart: chart_
        }
        port: "/dev/ttyACM0"
        bauds: 115200
        headers: ['demo.h']
    }

    Timer
    {
        interval: 50
        running: true
        repeat: true
        onTriggered:
        {
            if(ds_.dirty)
                ds_.refresh();
        }
    }
    ColumnLayout
    {
        anchors.fill: parent
        Text{text: "port: " + scope_.port}
        Text{text: "bauds: " + scope_.bauds}
        Text{text: "headers: " + scope_.headers}
        Button{text: "connect"; onClicked: scope_.beginListneing()}
        RowLayout
        {
            Layout.fillWidth: true
            Repeater
            {
                model: ds_.dataSources
                CheckBox
                {
                    text: modelData
                    onCheckedChanged: ds_.toggleDatasource(modelData)
                    Component.onCompleted: checked = true
                }
            }
        }
        ChartView
        {
            id: chart_
            
            title: "Simple FOC Scope"

            antialiasing: true
            Layout.fillHeight: true
            Layout.fillWidth: true

            function createSeriesWithLabel(label)
            {
                // critical to put the serie in var before returning to workaround a pyside6 bug
                return chart_.createSeries(ChartView.SeriesTypeLine, label, axisX, axisY); 

                // return line;
            }

            ValueAxis {
                id: axisY
                min: ds_.yMin
                max: ds_.yMax
            }

            ValueAxis {
                id: axisX
                min: ds_.xMin
                max: ds_.xMax

            }
        }
    }

}
