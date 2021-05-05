"""add strain name assoc table

Revision ID: f05fc486a0fd
Revises: 079dae11cc2f
Create Date: 2020-04-05 13:47:22.600573

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f05fc486a0fd'
down_revision = '079dae11cc2f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    assoc = op.create_table('strain_strain_name',
    sa.Column('strain_id', sa.Integer(), nullable=True),
    sa.Column('strain_name_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['strain_id'], ['strain.id'], name=op.f('fk_strain_strain_name_strain_id_strain')),
    sa.ForeignKeyConstraint(['strain_name_id'], ['strain_name.id'], name=op.f('fk_strain_strain_name_strain_name_id_strain_name'))
    )

    names = sa.Table(
        "strain_name",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("strain_id", sa.Integer)
    )

    connection = op.get_bind()

    values = [
        {"strain_id": name.strain_id, "strain_name_id": name.id}
        for name in connection.execute(names.select())
    ]

    op.bulk_insert(assoc, values)

    with op.batch_alter_table('strain_name', schema=None) as batch_op:
        batch_op.drop_constraint('fk_strain_name_strain_id_strain', type_='foreignkey')
        batch_op.drop_column('strain_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('strain_name', schema=None) as batch_op:
        batch_op.add_column(sa.Column('strain_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key('fk_strain_name_strain_id_strain', 'strain', ['strain_id'], ['id'])

    op.drop_table('strain_strain_name')
    # ### end Alembic commands ###
