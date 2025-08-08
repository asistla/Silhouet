import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, LabelList
} from 'recharts';
import { PERSONALITY_KEYS } from '../config';

interface Scores { [key: string]: number; }

interface ScoreChartProps {
    userScores: Scores;
    cohortScores: Scores;
}

// Custom Tick for Y-Axis to alternate labels
const AlternatingYAxisTick = (props: any) => {
    const { x, y, payload, index } = props;
    const isEven = index % 2 === 0;
    const tickX = isEven ? x - 15 : x + 15; // Position left or right
    const anchor = isEven ? 'end' : 'start'; // Anchor text accordingly

    return (
        <g transform={`translate(${x},${y})`}>
            <text x={isEven ? -10 : 10} y={0} dy={4} textAnchor={anchor} fill="#e8e4d5" fontSize={12}>
                {payload.value}
            </text>
        </g>
    );
};


const ScoreChart: React.FC<ScoreChartProps> = ({ userScores, cohortScores }) => {

    const chartData = PERSONALITY_KEYS.map((key) => ({
        subject: key.replace(/_/g, ' ').replace(' score', ''),
        user: userScores[`avg_${key}_score`] !== undefined ? userScores[`avg_${key}_score`] : 0,
        cohort: cohortScores[`avg_${key}_score`] !== undefined ? cohortScores[`avg_${key}_score`] : 0,
    }));

    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart 
                data={chartData} 
                layout="vertical" 
                margin={{ top: 5, right: 100, left: 100, bottom: 5 }} // Increased margins for labels
                barCategoryGap="30%"
            >
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e4d5" opacity={0.1} />
                <XAxis type="number" domain={[-1, 1]} tick={{ fill: '#e8e4d5' }} />
                <YAxis 
                    type="category" 
                    dataKey="subject" 
                    tickLine={false}
                    axisLine={false}
                    tick={<AlternatingYAxisTick />}
                    width={0} // Axis line is not needed, labels are positioned manually
                />
                <Tooltip
                    cursor={{fill: 'rgba(255, 255, 255, 0.05)'}}
                    contentStyle={{
                        backgroundColor: '#2d2d2d',
                        borderColor: '#4b3832',
                        color: '#e8e4d5',
                        fontFamily: 'Georgia, serif'
                    }}
                    labelStyle={{ color: '#c5b358' }}
                />
                <Legend wrapperStyle={{ color: '#e8e4d5', fontFamily: 'Garamond, serif', paddingTop: '10px' }} />
                <Bar 
                    name="My Scores" 
                    dataKey="user" 
                    fill="#b87333" 
                    radius={[0, 4, 4, 0]} // Slightly rounded bars
                />
                <Bar 
                    name="Cohort Scores" 
                    dataKey="cohort" 
                    fill="#a9a9a9" 
                    opacity={0.7} 
                    radius={[0, 4, 4, 0]}
                />
            </BarChart>
        </ResponsiveContainer>
    );
};

export default ScoreChart;